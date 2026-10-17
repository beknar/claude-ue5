"""random_dungeonmagic_level3: random_dungeonmagic_level2 with the Rogue: two daggers, a crossbow, a roll. Run 822 and
819 first.
First run (the level does not exist yet): opens random_dungeonmagic_level2 and saves it as
/Game/RandomDungeon/Maps/random_dungeonmagic_level3 (Save As), then stops: RESTART THE EDITOR and run it again. With the
copy there, it opens it and sets it up:
- the game mode BP_RDM3_GameMode (822: the Rogue, BP_RDM3_RogueCharacter, the dungeon HUD)
- her weapons, from 822's weapons.json: the daggers (drawn at the start: one in each hand, her three stabs with their
  blow times; carried on her thighs while the crossbow is drawn) and the crossbow (a spell weapon whose bolt is a mesh
  shot from its front, the next bolt on the rail; carried on her back while the daggers are drawn); flinch and death
- the roll (B, the gamepad's B): her RollF clip toward the way she moves, RollB backward when she stands; 4.2 m; blows
  miss her from 5 % to 75 % of it
- the HUD's status panel: her name; the controls (bCasterControls + bRogueControls) in the upper left, keyboard or
  gamepad by the device in use: 1 / 2 or the wheel (Y) switch, left mouse (RB) strikes or shoots, B rolls
Everything else is the magic levels' (the combat level's dungeon, monsters, blood, wounds, sound and music, the tactical
maps); the monsters' hit points and damage follow her average blow over the two. Args: none"""
import json, unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/random_dungeonmagic_level2"; MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level3"
JSON = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic3\weapons.json"
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
    print("RDM3 copied" if ok else "RDM3 copy FAILED", SRC, "->", MAP, "| restart the editor, then run 823 again")
else:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    D = json.load(open(JSON)); out = []
    def clips(d, wp):
        d.set_editor_property("attacks", [unreal.load_asset(a["clip"]) for a in wp["attacks"]]); d.set_editor_property("attack_starts", [0.0] * len(wp["attacks"]))
        d.set_editor_property("attack_ends", [float(a["end"]) for a in wp["attacks"]]); d.set_editor_property("hit_times", [float(a["hit"]) for a in wp["attacks"]])
        d.set_editor_property("get_hit", unreal.load_asset(wp["flinch"])); d.set_editor_property("death", unreal.load_asset(wp["death"]))
        assert all(d.attacks) and d.get_hit and d.death
    dg = D["weapons"]["Daggers"]; d = unreal.RDWeaponDef()
    d.set_editor_property("name", "Daggers"); d.set_editor_property("mesh", unreal.load_asset(dg["mesh"])); d.set_editor_property("hand_bone", dg["hand_bone"]); d.set_editor_property("grip", xf(dg["grip"]))
    d.set_editor_property("off_hand_mesh", unreal.load_asset(dg["off_mesh"])); d.set_editor_property("off_hand_bone", dg["off_bone"]); d.set_editor_property("off_hand_grip", xf(dg["off_grip"]))
    d.set_editor_property("holster_bone", dg["holster_bone"]); d.set_editor_property("holster_grip", xf(dg["holster"]))
    d.set_editor_property("off_hand_holster_bone", dg["off_holster_bone"]); d.set_editor_property("off_hand_holster_grip", xf(dg["off_holster"]))
    for k in ("damage", "reach", "arc"): d.set_editor_property(k, float(dg[k]))
    d.set_editor_property("play_rate", float(dg["rate"])); clips(d, dg)
    assert d.mesh and d.off_hand_mesh; out.append(d)
    X = D["weapons"]["Crossbow"]; d = unreal.RDWeaponDef()
    d.set_editor_property("name", "Crossbow"); d.set_editor_property("mesh", unreal.load_asset(X["mesh"])); d.set_editor_property("hand_bone", X["hand_bone"]); d.set_editor_property("grip", xf(X["grip"]))
    d.set_editor_property("holster_bone", X["holster_bone"]); d.set_editor_property("holster_grip", xf(X["holster"]))
    for k, v in (("damage", X["damage"]), ("reach", X["reach"]), ("arc", 0.0), ("play_rate", X["rate"]), ("bolt_speed", X["bolt_speed"]), ("bolt_turn_rate", X["bolt_turn"]),
                 ("bolt_splash", X["splash"]), ("bolt_effect_scale", X["trail_scale"]), ("burst_effect_scale", X["hit_scale"]), ("bolt_stick_seconds", X["stick"]),
                 ("spell_light_intensity", 0.0)):
        d.set_editor_property(k, float(v))
    d.set_editor_property("spell", True); d.set_editor_property("alongside", False)
    d.set_editor_property("bolt_effect", unreal.load_asset(X["trail"])); d.set_editor_property("burst_effect", unreal.load_asset(X["hit_fx"]))
    d.set_editor_property("bolt_mesh", unreal.load_asset(X["bolt_mesh"])); d.set_editor_property("bolt_mesh_transform", xf(X["bolt_xf"]))
    d.set_editor_property("bolt_from_weapon", True); d.set_editor_property("bolt_muzzle", V(*X["muzzle"]))
    d.set_editor_property("show_loaded_bolt", True); d.set_editor_property("loaded_bolt_transform", xf(X["loaded_xf"]))
    clips(d, X); assert d.mesh and d.bolt_mesh and d.bolt_effect and d.burst_effect; out.append(d)
    gen.set_editor_property("weapons", out)
    R = D["roll"]
    gen.set_editor_property("roll_clip", unreal.load_asset(R["forward"])); gen.set_editor_property("roll_back_clip", unreal.load_asset(R["back"]))
    gen.set_editor_property("roll_distance", 420.0); gen.set_editor_property("roll_cooldown", 0.25); gen.set_editor_property("roll_dodge", unreal.Vector2D(0.05, 0.75))
    assert gen.roll_clip and gen.roll_back_clip
    gen.set_editor_property("player_title", "ROGUE")
    gen.set_editor_property("caster_controls", True); gen.set_editor_property("rogue_controls", True); gen.set_editor_property("controls_hint", "")
    gen.set_editor_property("controls_keys", ["W A S D|move", "Mouse|look / turn the camera", "Space|jump", "R|switch walk / run", "Shift (held)|run",
                                               "B|roll / dodge", "1 / 2, wheel|daggers / crossbow", "Left mouse|strike or shoot", "F|open door or container", "M|map"])
    gen.set_editor_property("controls_pad", ["Left stick|move", "Right stick|look / turn the camera", "A|jump", "LT|switch walk / run",
                                              "B|roll / dodge", "Y|switch weapon", "RB|strike or shoot", "X|open door or container", "Back|map"])
    ws = w.get_world_settings(); ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/RandomDungeon/Blueprints/BP_RDM3_GameMode").generated_class())
    c = gen.get_start_room_center()
    for a in eas.get_all_level_actors():
        if isinstance(a, unreal.PlayerStart): a.set_actor_location(V(c.x, c.y, 100.0), False, False); a.set_actor_label("RDM3_PlayerStart")
    s0, s1 = unreal.IntPoint(0, 0), unreal.IntPoint(1, 0); back = gen.get_editor_property("weapons")
    print("RDM3 weapons: " + " | ".join(f"{b.name}: {b.damage:.0f} damage, reach {b.reach:.0f} cm, {len(b.attacks)} clips, spell={b.spell}, bolt mesh {b.bolt_mesh.get_name() if b.bolt_mesh else '-'}, holster {b.holster_bone}" for b in back)
          + f" | roll {gen.roll_clip.get_name()} / {gen.roll_back_clip.get_name()} | tactical maps {gen.tactical_maps} | game mode {ws.get_editor_property('default_game_mode').get_name()} | average blow {gen.get_average_weapon_damage():.1f}"
          f" | monsters: start {gen.get_monster_health(s0):.0f} hp / {gen.get_monster_damage(s0):.1f} dmg, generated {gen.get_monster_health(s1):.0f} hp / {gen.get_monster_damage(s1):.1f} dmg")
    les.save_current_level(); print("saved", MAP)
done()
