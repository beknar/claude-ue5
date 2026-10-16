"""random_dungeonmagic_level2: random_dungeonmagic_level with the dark caster: a sword in her right hand, fire from her
left. Run 817 first.
First run (the level does not exist yet): opens random_dungeonmagic_level and saves it as
/Game/RandomDungeon/Maps/random_dungeonmagic_level2 (Save As), then stops: RESTART THE EDITOR and run it again. With the
copy there, it opens it and sets it up:
- the game mode BP_RDM2_GameMode (817: girl-darkcaster-tripo, BP_RDM2_DarkCasterCharacter, the dungeon HUD)
- her weapons, from 817's weapons.json: the sword (drawn: Medieval_Weapons SM_Sword_1 in her right hand, her three cuts
  with their blow times) and the fire spell cast alongside it from her left hand (bAlongside: its own keys, the sword
  stays in her hand; the bolt, the effects and the numbers of random_dungeonmagic_level's spell); flinch and death
- the HUD's status panel: her name; the controls (bCasterControls) in the upper left, keyboard or gamepad by the device
  in use: as 811's, with left mouse / RB the sword and right mouse or E / LB the fire (run 819 first)
Everything else is the magic level's (the combat level's dungeon, monsters, blood, wounds, sound and music); the
monsters' hit points and damage follow her average blow over the two. Args: none"""
import json, unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/random_dungeonmagic_level"; MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level2"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic2\weapons.json"
V = unreal.Vector
def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
def xf(d): return unreal.Transform(V(*d["loc"]), unreal.Rotator(roll=d["rot"][0], pitch=d["rot"][1], yaw=d["rot"][2]), V(*d["scale"]))
if not eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    assert ues.get_editor_world().get_path_name().startswith(SRC + "."), ues.get_editor_world().get_path_name()
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("RDM2 copied" if ok else "RDM2 copy FAILED", SRC, "->", MAP, "| restart the editor, then run 818 again")
else:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    D = json.load(open(JSON)); out = []
    sw = D["weapons"]["Sword"]; d = unreal.RDWeaponDef()
    d.set_editor_property("name", "Sword"); d.set_editor_property("mesh", unreal.load_asset(sw["mesh"])); d.set_editor_property("hand_bone", sw["hand_bone"]); d.set_editor_property("grip", xf(sw["grip"]))
    for k in ("damage", "reach", "arc"): d.set_editor_property(k, float(sw[k]))
    d.set_editor_property("play_rate", float(sw["rate"]))
    d.set_editor_property("attacks", [unreal.load_asset(a["clip"]) for a in sw["attacks"]]); d.set_editor_property("attack_starts", [0.0] * len(sw["attacks"]))
    d.set_editor_property("attack_ends", [float(a["end"]) for a in sw["attacks"]]); d.set_editor_property("hit_times", [float(a["hit"]) for a in sw["attacks"]])
    d.set_editor_property("get_hit", unreal.load_asset(sw["flinch"])); d.set_editor_property("death", unreal.load_asset(sw["death"]))
    assert d.mesh and all(d.attacks) and d.get_hit and d.death; out.append(d)
    S = D["weapons"]["Fire"]; d = unreal.RDWeaponDef()
    d.set_editor_property("name", "Fire"); d.set_editor_property("mesh", None)
    for k, v in (("damage", S["damage"]), ("reach", S["reach"]), ("arc", 360.0), ("play_rate", S["rate"]), ("bolt_speed", S["bolt_speed"]), ("bolt_turn_rate", S["bolt_turn"]),
                 ("bolt_splash", S["splash"]), ("charge_effect_scale", S["charge_scale"]), ("bolt_effect_scale", S["bolt_scale"]), ("burst_effect_scale", S["burst_scale"]),
                 ("burst_flame_effect_scale", S["burst_flame_scale"]), ("burst_flame_seconds", S["burst_flame_seconds"]), ("spell_light_intensity", S["light_cd"])):
        d.set_editor_property(k, float(v))
    d.set_editor_property("spell", True); d.set_editor_property("alongside", True); d.set_editor_property("spell_bone", S["bone"])
    for k, p in (("charge_effect", S["charge"]), ("bolt_effect", S["bolt"]), ("burst_effect", S["burst"]), ("burst_flame_effect", S["burst_flame"])):
        a = unreal.load_asset(p); assert a, p; d.set_editor_property(k, a)
    d.set_editor_property("spell_light_color", unreal.LinearColor(*S["light"], 1.0))
    d.set_editor_property("attacks", [unreal.load_asset(c["clip"]) for c in S["casts"]]); d.set_editor_property("attack_starts", [0.0] * len(S["casts"]))
    d.set_editor_property("attack_ends", [float(c["end"]) for c in S["casts"]]); d.set_editor_property("hit_times", [float(c["hit"]) for c in S["casts"]])
    d.set_editor_property("get_hit", unreal.load_asset(S["flinch"])); d.set_editor_property("death", unreal.load_asset(S["death"]))
    assert all(d.attacks); out.append(d)
    gen.set_editor_property("weapons", out)
    gen.set_editor_property("player_title", "GIRL-DARKCASTER")
    # the controls (as 811's): the magic levels' layout, shown in the HUD's upper left for the device in use
    gen.set_editor_property("caster_controls", True); gen.set_editor_property("controls_hint", "")
    gen.set_editor_property("controls_keys", ["W A S D|move", "Mouse|look / turn the camera", "Space|jump", "R|switch walk / run", "Shift (held)|run",
                                               "Left mouse|sword", "Right mouse / E|fire spell", "F|open door or container", "M|map"])
    gen.set_editor_property("controls_pad", ["Left stick|move", "Right stick|look / turn the camera", "A|jump", "LT|switch walk / run",
                                              "RB|sword", "LB|fire spell", "X|open door or container", "Back|map"])
    ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/RandomDungeon/Blueprints/BP_RDM2_GameMode").generated_class())
    c = gen.get_start_room_center()
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart): a.set_actor_location(V(c.x, c.y, 100.0), False, False); a.set_actor_label("RDM2_PlayerStart")
    s0, s1 = unreal.IntPoint(0, 0), unreal.IntPoint(1, 0); back = gen.get_editor_property("weapons")
    print("RDM2 weapons: " + " | ".join(f"{b.name}: {b.damage:.0f} damage, reach {b.reach:.0f} cm, {len(b.attacks)} clips, spell={b.spell}, alongside={b.alongside}, bone {b.spell_bone if b.spell else b.hand_bone}" for b in back)
          + f" | game mode {ws.get_editor_property('default_game_mode').get_name()} | average blow {gen.get_average_weapon_damage():.1f}"
          f" | monsters: start {gen.get_monster_health(s0):.0f} hp / {gen.get_monster_damage(s0):.1f} dmg, generated {gen.get_monster_health(s1):.0f} hp / {gen.get_monster_damage(s1):.1f} dmg")
    les.save_current_level(); print("saved", MAP)
done()
