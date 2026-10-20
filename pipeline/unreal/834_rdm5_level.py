"""random_dungeonmagic_level5: random_dungeonmagic_level (the Mage's) with the Summoner in her place, her face moving.
Run 833 and 819 first.
First run (the level does not exist yet): opens random_dungeonmagic_level and saves it as
/Game/RandomDungeon/Maps/random_dungeonmagic_level5 (Save As: a map is never duplicated), then stops: RESTART THE EDITOR and
run it again. With the copy there, it opens it and sets it up:
- the game mode BP_RDM5_GameMode (833: the Summoner, BP_RDM5_SummonerCharacter, with the dungeon HUD)
- her one weapon is the Mage's fire spell (833's spell.json: the Mage's numbers and effects, the Summoner's own three casts
  with their release times, her flinch and death)
- her name on the HUD, the magic levels' controls (bCasterControls), as the Mage's level has them
- her face (SourceArt/summoner/face.json): the expression channels (the morph targets and painted patches each sets) and
  the occasions that show them (Hurt, Cast, Loot as cues; Fight, LowHealth, Death held) -> the generator's FaceChannels /
  FaceCues, which give her pawn a URDFaceComponent in play
- the face camera for the test (812's face step): a SceneCapture2D tagged RDM5_FaceCam rendering into
  /Game/RandomDungeon/Magic5/RT_RDM5_Face (256 x 256), capturing only when asked (the test puts it in front of her face)
Everything else is the Mage's level's: the dungeon, its start section, the monsters, blood, wounds, sound, music, the
tactical maps. Args: none"""
import json, unreal
eal = unreal.EditorAssetLibrary
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/RandomDungeon/Maps/random_dungeonmagic_level"; MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
V = unreal.Vector
def done():
    import gc
    for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
    gc.collect()
if not eal.does_asset_exist(MAP):
    if not ues.get_editor_world().get_path_name().startswith(SRC + "."): les.load_level(SRC)
    assert ues.get_editor_world().get_path_name().startswith(SRC + "."), ues.get_editor_world().get_path_name()
    ok = unreal.EditorLoadingAndSavingUtils.save_map(ues.get_editor_world(), MAP)
    print("RDM5 copied" if ok else "RDM5 copy FAILED", SRC, "->", MAP, "| restart the editor, then run 834 again")
else:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
    gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    S = json.load(open(SA + r"\random_dungeon_magic5\spell.json"))
    # the Mage's spell as her level has it, with the Summoner's clips
    d = gen.get_editor_property("weapons")[0]
    d.set_editor_property("attacks", [unreal.load_asset(c["clip"]) for c in S["casts"]])
    d.set_editor_property("attack_starts", [0.0 for c in S["casts"]]); d.set_editor_property("attack_ends", [float(c["end"]) for c in S["casts"]])
    d.set_editor_property("hit_times", [float(c["hit"]) for c in S["casts"]])
    d.set_editor_property("get_hit", unreal.load_asset(S["flinch"])); d.set_editor_property("death", unreal.load_asset(S["death"]))
    assert all(d.attacks) and d.get_hit and d.death
    gen.set_editor_property("weapons", [d])
    gen.set_editor_property("player_title", "SUMMONER")
    # her face
    F = json.load(open(SA + r"\summoner\face.json"))
    chans = []
    for name, c in F["channels"].items():
        ch = unreal.RDFaceChannel(); ch.set_editor_property("name", name)
        ch.set_editor_property("morphs", {k: float(v) for k, v in c["morphs"].items()}); ch.set_editor_property("params", {k: float(v) for k, v in c["params"].items()})
        chans.append(ch)
    cues = {}
    for occ, c in F["cues"].items():
        q = unreal.RDFaceCue()
        q.set_editor_property("weight", float(c["weight"])); q.set_editor_property("fade_in", float(c["in"]))
        q.set_editor_property("hold", float(c["hold"])); q.set_editor_property("fade_out", float(c["out"]))
        q.set_editor_property("channel", c["channel"]); cues[occ] = q
    gen.set_editor_property("face_channels", chans); gen.set_editor_property("face_cues", cues)
    ws = w.get_world_settings()
    ws.set_editor_property("default_game_mode", unreal.load_asset("/Game/RandomDungeon/Blueprints/BP_RDM5_GameMode").generated_class())
    # the face camera (a test cannot spawn into a play world: it is placed here and found by its tag)
    RT = "/Game/RandomDungeon/Magic5/RT_RDM5_Face"
    rt = unreal.load_asset(RT)
    if not rt:
        rt = unreal.AssetToolsHelpers.get_asset_tools().create_asset("RT_RDM5_Face", "/Game/RandomDungeon/Magic5", unreal.TextureRenderTarget2D, unreal.TextureRenderTargetFactoryNew())
    rt.set_editor_property("size_x", 256); rt.set_editor_property("size_y", 256)
    rt.set_editor_property("render_target_format", unreal.TextureRenderTargetFormat.RTF_RGBA8)
    rt.set_editor_property("clear_color", unreal.LinearColor(0, 0, 0, 1)); eal.save_loaded_asset(rt, only_if_is_dirty=False)
    for a in eas.get_all_level_actors():
        if a.actor_has_tag("RDM5_FaceCam"): eas.destroy_actor(a)
    cam = eas.spawn_actor_from_class(unreal.SceneCapture2D, V(0, 0, -5000))
    cam.tags = ["RDM5_FaceCam"]; cam.set_actor_label("RDM5_FaceCam")
    cc = cam.capture_component2d
    cc.set_editor_property("texture_target", rt); cc.set_editor_property("capture_every_frame", False); cc.set_editor_property("capture_on_movement", False)
    cc.set_editor_property("fov_angle", 28.0); cc.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    back = gen.get_editor_property("weapons")[0]
    print(f"RDM5 spell {back.name}: {back.damage:.0f} damage, reach {back.reach:.0f} cm, {len(back.attacks)} casts ({', '.join(a.get_name() for a in back.attacks)}),"
          f" bolt at " + ", ".join(f"{h:.2f}" for h in back.hit_times) + f" s | flinch {back.get_hit.get_name()} death {back.death.get_name()}"
          f" | face: {len(gen.get_editor_property('face_channels'))} channels, cues {sorted(str(k) for k in gen.get_editor_property('face_cues').keys())}"
          f" | game mode {ws.get_editor_property('default_game_mode').get_name()}")
    les.save_current_level()
    print("saved", MAP)
done()
