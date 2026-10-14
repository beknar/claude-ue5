"""random_dungeoncombat_level: random_dungeon_level with fighting. Run 770 (the dungeon) and 790 (her weapons) first.
First run (the level does not exist yet): opens random_dungeon_level and saves it as
/Game/RandomDungeon/Maps/random_dungeoncombat_level (Save As: a map is never duplicated), then stops: RESTART THE EDITOR
and run it again. With the copy there, it opens it and sets up its dungeon generator:
- bCombat: the player (jrpg-fem5-tripo, BP_RD_GameMode as in random_dungeon_level) gets 100 hit points and the three
  weapons of 790's weapons.json (meshes, grips, damage, reach, arc, clips with their hit times)
- monsters in 30% of the rooms; each kind gets its attack, flinch and death clips (Creatures_Pack), the time into each
  attack clip at which the blow lands (where the creature's fastest bone peaks), and its factors: hit points and
  damage against the average monster, reach, seconds between attacks
- the tiers: the average monster of the start section (the first 252 m square) has 50% of her hit points and does 45%
  of her average blow; in every section generated in play it is on a par with her (100% / 100%)
- bStylizedMap: the minimap and the M map are drawn as a miniature of the dungeon
- the PlayerStart is put in the middle of the start section (the great hall)
The start section itself is the saved one of random_dungeon_level (same seed, same rooms); sections generated in play
are never saved. Prints the numbers. Args: none"""
import json, os, unreal
eal = unreal.EditorAssetLibrary; APE = unreal.AnimPoseExtensions
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/random_dungeon_level"; MAP = "/Game/RandomDungeon/Maps/random_dungeoncombat_level"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_combat\weapons.json"
V = unreal.Vector
def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
if not eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    assert ues.get_editor_world().get_path_name().startswith(SRC + "."), ues.get_editor_world().get_path_name()
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("RDC copied" if ok else "RDC copy FAILED", SRC, "->", MAP, "| restart the editor, then run 791 again")
else:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    # ---- her weapons
    D = json.load(open(JSON))
    def xf(d): return unreal.Transform(V(*d["loc"]), unreal.Rotator(roll=d["rot"][0], pitch=d["rot"][1], yaw=d["rot"][2]), V(*d["scale"]))
    WPN = []
    for name in D["order"]:
        e = D["weapons"][name]; d = unreal.RDWeaponDef()
        d.set_editor_property("name", name); d.set_editor_property("mesh", unreal.load_asset(e["mesh"])); d.set_editor_property("hand_bone", e["hand_bone"]); d.set_editor_property("grip", xf(e["grip"]))
        if e["shield"]:
            d.set_editor_property("off_hand_mesh", unreal.load_asset(e["shield"])); d.set_editor_property("off_hand_bone", e["shield_bone"]); d.set_editor_property("off_hand_grip", xf(e["shield_grip"]))
        for k in ("damage", "reach", "arc"): d.set_editor_property(k, float(e[k]))
        d.set_editor_property("play_rate", float(e["rate"]))
        d.set_editor_property("attacks", [unreal.load_asset(a["clip"]) for a in e["attacks"]])
        d.set_editor_property("attack_starts", [0.0 for a in e["attacks"]]); d.set_editor_property("attack_ends", [float(a["end"]) for a in e["attacks"]])
        d.set_editor_property("hit_times", [float(a["hit"]) for a in e["attacks"]])
        d.set_editor_property("get_hit", unreal.load_asset(e["flinch"])); d.set_editor_property("death", unreal.load_asset(e["death"]))
        assert d.mesh and all(d.attacks) and d.get_hit and d.death, name
        WPN.append(d)
        print(f"  weapon {name}: {e['damage']:.0f} damage, reach {e['reach']:.0f} cm, arc {e['arc']:.0f}, {len(e['attacks'])} attack clips at rate {e['rate']}" + (", shield" if e["shield"] else ""))
    # ---- the monsters fight: attack / flinch / death clips, blow times, factors (hit points, damage, reach cm, seconds between attacks)
    FACT = {"Troll": (1.4, 1.3, 130.0, 1.9), "Daemon": (1.1, 1.1, 110.0, 1.6), "Horned": (1.2, 1.15, 115.0, 1.7), "Ripper_dog": (0.7, 0.8, 95.0, 1.2), "Spider": (0.6, 0.7, 100.0, 1.3),
            "Mutant": (1.0, 1.0, 110.0, 1.6)}
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    clips = {str(a.asset_name): str(a.package_name) for a in ar.get_assets_by_path("/Game/Creatures_Pack", recursive=True) if str(a.asset_class_path.asset_name) == "AnimSequence"}
    o = unreal.AnimPoseEvaluationOptions()
    def blow_time(anim):
        """the time the creature's fastest bone peaks (its claw, jaw or weapon arm): where the blow lands"""
        L = unreal.AnimationLibrary.get_sequence_length(anim); n = 30
        names = APE.get_bone_names(APE.get_anim_pose_at_time(anim, 0.0, o))
        pts = [[APE.get_bone_pose(p, b, unreal.AnimPoseSpaces.WORLD).translation for b in names] for p in (APE.get_anim_pose_at_time(anim, L * k / n, o) for k in range(n + 1))]
        sp = [max((pts[k + 1][i] - pts[k][i]).length() for i in range(len(names))) / (L / n) for k in range(n)]
        sm = [sum(sp[max(0, k - 1):k + 2]) / len(sp[max(0, k - 1):k + 2]) for k in range(n)]
        k = max(range(n), key=lambda i: sm[i])
        return min(max(L * (k + 0.5) / n, 0.15), L - 0.1), L
    MON = []
    for old in gen.get_editor_property("monsters"):
        name = str(old.name); d = unreal.RDMonsterDef()
        for k in ("name", "mesh", "idle", "walk", "walk_speed", "walk_clip_speed", "capsule_radius", "capsule_half_height", "mesh_z", "mesh_yaw", "scale", "weight",
                  "sound_set", "step_length"): d.set_editor_property(k, old.get_editor_property(k))      # (the last two are 797's: a re-run here must not silence the monsters)
        att = [unreal.load_asset(clips[c]) for c in sorted(clips) if c.startswith(f"Anim_{name}_Attack")]
        short = [a for a in att if unreal.AnimationLibrary.get_sequence_length(a) <= 2.8]                 # (the long clips are combinations: one blow counts)
        att = (short or sorted(att, key=unreal.AnimationLibrary.get_sequence_length)[:1])[:3]
        hits = [blow_time(a) for a in att]
        hf, df, reach, gap = FACT.get(name, (1.0, 1.0, 110.0, 1.6))
        d.set_editor_property("attacks", att); d.set_editor_property("hit_times", [h for h, _ in hits])
        d.set_editor_property("get_hit", unreal.load_asset(clips.get(f"Anim_{name}_GetHit", "")) if f"Anim_{name}_GetHit" in clips else None)
        d.set_editor_property("death", unreal.load_asset(clips.get(f"Anim_{name}_Death", "")) if f"Anim_{name}_Death" in clips else None)
        d.set_editor_property("health_factor", hf); d.set_editor_property("damage_factor", df); d.set_editor_property("reach", reach); d.set_editor_property("attack_interval", gap)
        assert att and d.get_hit and d.death, (name, len(att))
        MON.append(d)
        print(f"  monster {name}: {len(att)} attack clips, blows at " + ", ".join(f"{h:.2f} of {L:.2f} s" for h, L in hits) + f" | x{hf} hit points, x{df} damage, reach {reach:.0f} cm, an attack every {gap} s")
    for k, v in (("combat", True), ("stylized_map", True), ("monster_coverage", 0.3), ("player_max_health", 100.0), ("weapons", WPN), ("monsters", MON), ("start_monster_health", 0.5),
                 ("start_monster_damage", 0.45), ("runtime_monster_health", 1.0), ("runtime_monster_damage", 1.0)):
        gen.set_editor_property(k, v)
    # ---- she starts in the middle of the start section
    c = gen.get_start_room_center()
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart): a.set_actor_location(V(c.x, c.y, 100.0), False, False); a.set_actor_label("RDC_PlayerStart")
    avg = gen.get_average_weapon_damage(); hp = gen.get_editor_property("player_max_health")
    s0, s1 = unreal.IntPoint(0, 0), unreal.IntPoint(1, 0)
    wsum = sum(m.weight for m in MON); mh = sum(m.weight * m.health_factor for m in MON) / wsum; md = sum(m.weight * m.damage_factor for m in MON) / wsum
    print(f"player: {hp:.0f} hit points, average blow {avg:.1f} | start section monsters: average {gen.get_monster_health(s0):.0f} hit points, {gen.get_monster_damage(s0):.1f} damage"
          f" | generated sections: average {gen.get_monster_health(s1):.0f} hit points, {gen.get_monster_damage(s1):.1f} damage | coverage {gen.get_editor_property('monster_coverage'):.0%}")
    for m in MON:
        print(f"    {m.name}: start {round(gen.get_monster_health(s0) * m.health_factor / mh)} hp / {round(gen.get_monster_damage(s0) * m.damage_factor / md)} dmg"
              f" | generated {round(gen.get_monster_health(s1) * m.health_factor / mh)} hp / {round(gen.get_monster_damage(s1) * m.damage_factor / md)} dmg")
    print("player start", round(c.x), round(c.y), "| start section", gen.get_section(s0) is not None)
    les.save_current_level()
    print("saved", MAP)
done()
