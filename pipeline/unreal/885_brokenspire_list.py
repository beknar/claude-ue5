"""The user's list of 2026-11-02 (after Brokenspire's reel): "run is no longer mapped to the gamepad. make LB the block button
for the warrior and make LT to activate run. the castle's outer walls look strange being covered with arches ... create a day
night cycle where a full day can elapse within a half hour. the overhead village map should look more like [ai models/fairhill
village.jpg]".
- the Warrior's gamepad list on mistward_castle, brokenspire and random_dungeonmagic_level5 (the maps 870 wrote it on):
  "LT|switch walk / run" and "LB (hold)|block with the shield" (the C++: URDCombatComponent::TickBlocking holds the right
  mouse button or LB; LT switches every hero's run). A rerun of 870's filter had dropped her run line altogether.
- brokenspire: its day and night (bDayNight, DayLengthSeconds 1800: a day in half an hour of play; the morning's 8 o'clock
  for a new game; RD/RDTownDay.cpp)
- the hero menu's music (the second list of 2026-11-02): SourceArt/mistward/menu_sounds.json, converted first with
  blender_numpy/rdc_sound_prep.py into SourceArt/mistward/audio_menu/; imported looping and set on mistward_castle_select's
  RDHeroSelect (MenuMusic)
Then run 882 (the castle's and the town wall's new pieces, the town built again) and 883 with the colour map's pictures.
Args: none"""
import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = ["/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/brokenspire", "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"]


def warrior_pad(pad):
    """her list: no block on LT, no run on L3; LT runs (fourth), LB held blocks (after it)"""
    pad = [k for k in pad if not k.startswith(("LT (hold)|", "L3|", "LT|", "LB (hold)|"))]
    pad.insert(min(len(pad), 3), "LT|switch walk / run")
    pad.insert(min(len(pad), 4), "LB (hold)|block with the shield")
    return pad


for MAP in MAPS:
    if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    heroes = list(g.get_editor_property("heroes"))
    for h in heroes:
        if str(h.name) == "Warrior": h.controls_pad = warrior_pad(list(h.controls_pad))
    g.set_editor_property("heroes", heroes)
    w = next(h for h in g.get_editor_property("heroes") if str(h.name) == "Warrior")
    print("885", MAP.split("/")[-1], "Warrior pad:", list(w.controls_pad))
    if MAP.endswith("brokenspire"):
        for k, v in (("day_night", True), ("day_length_seconds", 1800.0), ("town_start_hour", 8.0), ("day_max_sun_elevation", 62.0),
                     # (the moon at 0.5 lux left the wall walk, which has no lamps, nearly black: 1.0)
                     ("moon_lux", 1.0)):
            g.set_editor_property(k, v)
        print("885 brokenspire day and night:", g.get_editor_property("day_night"), g.get_editor_property("day_length_seconds"), "s a day")
    les.save_current_level()
# ---- the Warrior's block over her walk (the second list: "when the warrior blocks with her shield and moves back or forwards
# or left and right, her legs should still be moving"): her AnimBP gets a layered blend from spine_01 up between its slot and
# its foot IK, the block clip held at its moment there, weighted by a float BlockAlpha the combat component eases (the
# whole-body held montage stopped her legs). Idempotent: a layered blend already there is left as it is.
import editor_toolset.toolsets.blueprint as BT
T = BT.BlueprintTools
ABP = "/Game/JRPG/Warrior3Locomotion/ABP_Unarmed_Warrior3"
abp = unreal.load_asset(ABP)
ag = {x.get_name(): x for x in T.list_graphs(abp)}["AnimGraph"]
nodes = T.find_nodes(ag, "")
def pin(n, nm, out):
    i = T.get_node_infos([n])[0]
    for p in (i.output_pins if out else i.input_pins):
        if str(p.name) == nm: return p
    raise KeyError((n.get_name(), nm, [str(p.name) for p in (i.output_pins if out else i.input_pins)]))
if any(n.get_class().get_name() == "AnimGraphNode_LayeredBoneBlend" for n in nodes):
    print("885 block layer: already in", ABP)
else:
    if "BlockAlpha" not in [str(v) for v in T.list_variables(abp)]: T.add_variable(abp, "BlockAlpha", "float")
    slot = next(n for n in nodes if n.get_class().get_name() == "AnimGraphNode_Slot")
    rig = next(n for n in nodes if n.get_class().get_name() == "AnimGraphNode_ControlRig")
    sp = pin(slot, "Pose", True)
    for q in sp.get_editor_property("connected_pins"): T.break_pins(sp.pin_id, q)
    lb = T.create_node(ag, "Animation|Blends|Layeredblendperbone", unreal.IntPoint(200, 300))
    ev = T.create_node(ag, "Animation|Sequences|Evaluate'AS_Warrior3_Box_03'", unreal.IntPoint(-100, 500))
    gv = [t_ for t_ in [str(x) for x in T.find_node_types(ag, "BlockAlpha")] if "Get" in t_]
    va = T.create_node(ag, gv[0], unreal.IntPoint(-100, 650))
    # (the branch from spine_01 down the chain: arms, head, the shield's hand; her legs and hips stay her locomotion's)
    nd = lb.get_editor_property("node"); nd.import_text('(LayerSetup=((BranchFilters=((BoneName="spine_01",BlendDepth=0)))),bMeshSpaceRotationBlend=True)'); lb.set_editor_property("node", nd)
    lbi = T.get_node_infos([lb])[0]
    print("885 block layer pins", [str(p.name) for p in lbi.input_pins], [str(p.name) for p in lbi.output_pins])
    T.connect_pins(sp.pin_id, pin(lb, "BasePose", False).pin_id)
    T.connect_pins(pin(ev, "Pose", True).pin_id, pin(lb, "BlendPoses_0", False).pin_id)
    T.connect_pins(pin(va, "BlockAlpha", True).pin_id, pin(lb, "BlendWeights_0", False).pin_id)
    T.connect_pins(pin(lb, "Pose", True).pin_id, pin(rig, "Source", False).pin_id)
    # (the clip's moment the generator holds: BlockClipTime, 1.6 s)
    try: T.set_pin_value(ev, "ExplicitTime", "1.6")
    except Exception as e:
        en = ev.get_editor_property("node"); en.import_text("(ExplicitTime=1.6)"); ev.set_editor_property("node", en); print("885 explicit time by the node's text:", e)
    ok = unreal.BlueprintEditorLibrary.compile_blueprint(abp); unreal.EditorAssetLibrary.save_loaded_asset(abp, only_if_is_dirty=False)
    back = [n.get_class().get_name() for n in T.find_nodes(ag, "")]
    print("885 block layer: compiled", ok, "| nodes", back, "| layer", lb.get_editor_property("node").export_text()[:200])
# ---- the hero menu's music (the user's of 2026-11-02, the second list: "pick thematic music for the choose your hero starting
# screen. this should be different from the music for inside the dungeon"): SourceArt/mistward/menu_sounds.json converted by
# rdc_sound_prep.py into SourceArt/mistward/audio_menu/ (ignored), imported looping, set on the menu's RDHeroSelect
import os, json
AUD = r"E:\code\claude-ue5\claude_ue5\SourceArt\mistward\audio_menu"
idx = os.path.join(AUD, "index.json")
if os.path.exists(idx):
    files = [os.path.join(AUD, f) for f in sorted(os.listdir(AUD)) if f.startswith("Music_Menu_") and f.endswith(".wav")]
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", files[0]); t.set_editor_property("destination_path", "/Game/RandomDungeon/Audio/Menu")
    t.set_editor_property("destination_name", "SW_Music_Menu"); t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True); t.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    snd = unreal.load_asset("/Game/RandomDungeon/Audio/Menu/SW_Music_Menu")
    snd.set_editor_property("looping", True); unreal.EditorAssetLibrary.save_loaded_asset(snd, False)
    MENU = "/Game/RandomDungeon/Maps/mistward_castle_select"
    les.load_level(MENU)
    sel = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDHeroSelect))
    sel.set_editor_property("menu_music", snd); sel.set_editor_property("menu_music_volume", 0.8)
    les.save_current_level()
    print("885 menu music:", snd.get_name(), round(snd.get_editor_property("duration"), 1), "s, looping", snd.get_editor_property("looping"), "on", sel.get_name())
else:
    print("885 menu music: no", idx, "(run rdc_sound_prep.py SourceArt/mistward/menu_sounds.json SourceArt/mistward/audio_menu first)")
les.load_level(MAPS[1])
import gc
del g, heroes, w
gc.collect()
