"""random_dungeonmagic_level: random_dungeoncombat_level with a fire caster instead of the swordswoman. Run 810 first.
First run (the level does not exist yet): opens random_dungeoncombat_level and saves it as
/Game/RandomDungeon/Maps/random_dungeonmagic_level (Save As: a map is never duplicated), then stops: RESTART THE EDITOR
and run it again. With the copy there, it opens it and sets it up:
- the game mode BP_RDM_GameMode (810: girl-caster-tripo, BP_RDM_CasterCharacter, with the dungeon HUD)
- her one weapon is the fire spell of 810's spell.json (FRDWeaponDef with bSpell: the three cast clips with their release
  times, the bolt's speed, steering, reach and splash, the charge / bolt / burst effects and the bolt's light); her
  flinch and death clips
- the HUD's status panel: her name; the controls (bCasterControls) in the upper left, keyboard or gamepad by the device
  in use: WASD / left stick move, mouse / right stick look, Space / A jump, R / LT switch walk and run (Shift held runs),
  left mouse or E / LB or RB the fire spell, F / X open (run 819 first: her character's RunMode)
Everything else is the combat level's: the dungeon, its saved start section, the monsters with their clips and tiers
(a monster's hit points and damage follow her average blow: the spell's damage), blood, wounds, sound, music, the
stylised maps. Run 797 on this level after it to give it the spell's sounds. Args: none"""
import json, unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/random_dungeoncombat_level"; MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic\spell.json"
V = unreal.Vector
def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
if not eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    assert ues.get_editor_world().get_path_name().startswith(SRC + "."), ues.get_editor_world().get_path_name()
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("RDM copied" if ok else "RDM copy FAILED", SRC, "->", MAP, "| restart the editor, then run 811 again")
else:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    S = json.load(open(JSON))
    d = unreal.RDWeaponDef()
    d.set_editor_property("name", S["name"]); d.set_editor_property("mesh", None); d.set_editor_property("off_hand_mesh", None)
    for k, v in (("damage", S["damage"]), ("reach", S["reach"]), ("arc", 360.0), ("play_rate", S["rate"]), ("bolt_speed", S["bolt_speed"]), ("bolt_turn_rate", S["bolt_turn"]),
                 ("bolt_splash", S["splash"]), ("charge_effect_scale", S["charge_scale"]), ("bolt_effect_scale", S["bolt_scale"]), ("burst_effect_scale", S["burst_scale"]),
                 ("burst_flame_effect_scale", S["burst_flame_scale"]), ("burst_flame_seconds", S["burst_flame_seconds"]), ("spell_light_intensity", S["light_cd"])):
        d.set_editor_property(k, float(v))
    d.set_editor_property("spell", True); d.set_editor_property("spell_bone", S["bone"])
    for k, p in (("charge_effect", S["charge"]), ("bolt_effect", S["bolt"]), ("burst_effect", S["burst"]), ("burst_flame_effect", S["burst_flame"])):
        a = unreal.load_asset(p); assert a, p; d.set_editor_property(k, a)
    d.set_editor_property("spell_light_color", unreal.LinearColor(*S["light"], 1.0))
    d.set_editor_property("attacks", [unreal.load_asset(c["clip"]) for c in S["casts"]])
    d.set_editor_property("attack_starts", [0.0 for c in S["casts"]]); d.set_editor_property("attack_ends", [float(c["end"]) for c in S["casts"]])
    d.set_editor_property("hit_times", [float(c["hit"]) for c in S["casts"]])
    d.set_editor_property("get_hit", unreal.load_asset(S["flinch"])); d.set_editor_property("death", unreal.load_asset(S["death"]))
    assert all(d.attacks) and d.get_hit and d.death
    gen.set_editor_property("weapons", [d])
    gen.set_editor_property("player_title", "GIRL-CASTER")
    # the controls: the magic levels' layout (URDCombatComponent with bCasterControls; 819 gives her character RunMode), shown
    # in the HUD's upper left for the device in use ("key|what it does"); the old one-line hint under the status panel goes
    gen.set_editor_property("caster_controls", True); gen.set_editor_property("controls_hint", "")
    gen.set_editor_property("controls_keys", ["W A S D|move", "Mouse|look / turn the camera", "Space|jump", "R|switch walk / run", "Shift (held)|run",
                                               "Left mouse / E|fire spell", "F|open door or container", "M|map"])
    gen.set_editor_property("controls_pad", ["Left stick|move", "Right stick|look / turn the camera", "A|jump", "LT|switch walk / run",
                                              "LB / RB|fire spell", "X|open door or container"])
    ws = w.get_world_settings()
    ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/RandomDungeon/Blueprints/BP_RDM_GameMode").generated_class())
    c = gen.get_start_room_center()
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart): a.set_actor_location(V(c.x, c.y, 100.0), False, False); a.set_actor_label("RDM_PlayerStart")
    s0, s1 = unreal.IntPoint(0, 0), unreal.IntPoint(1, 0)
    back = gen.get_editor_property("weapons")[0]
    print(f"RDM spell {back.name}: spell={back.spell}, {back.damage:.0f} damage, reach {back.reach:.0f} cm, bolt {back.bolt_speed:.0f} cm/s, splash {back.bolt_splash:.0f} cm,"
          f" {len(back.attacks)} casts at rate {back.play_rate} (bolt at " + ", ".join(f"{h:.2f}" for h in back.hit_times) + " s)"
          f" | effects {back.charge_effect.get_name()} / {back.bolt_effect.get_name()} / {back.burst_effect.get_name()} + {back.burst_flame_effect.get_name()}"
          f" | game mode {ws.get_editor_property('default_game_mode').get_name()}"
          f" | monsters: start section {gen.get_monster_health(s0):.0f} hp / {gen.get_monster_damage(s0):.1f} dmg, generated {gen.get_monster_health(s1):.0f} hp / {gen.get_monster_damage(s1):.1f} dmg")
    les.save_current_level()
    print("saved", MAP)
done()
