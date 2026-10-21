"""random_dungeonmagic_level5 as a level with heroes to choose from: level 4's (its Save As copy: the four heroes, mana,
potions and food, the inventory, the painted interface) with a fifth hero, the Summoner (Summoner3), and armour to find.
Run after 600-620 for Summoner3, 849-851 (the armour), and with random_dungeonmagic_level5 made by Save As from
random_dungeonmagic_level4 (restart the editor after the Save As). Then 819, 826 with 5 (the menu level), the armour's
pictures (830 --level 5) and the test (853 through 828_rdm4.ps1 -lv 5).
- BP_RDM5_Summoner3Character: her dungeon character, a child of BP_JRPGSummoner3Character (620) with the casters' 36 cm
  capsule (819 gives her RunMode and the walk / run switch)
- the generator's Heroes: level 4's four, and the Summoner (SourceArt/random_dungeon_magic5/summoner_hero.json): the Mage's
  fire and dark fire as level 4 has them, cast with her own clips (each bolt released where her right hand moves fastest,
  as 833 measures; her flinch and death), her hit points, mana, card lines; the Mage's controls and an armour line
- Items: level 4's, and the five armour sets (SourceArt/summoner3/armour.json): kind Armour, the share of a blow each
  takes off, weight 0 (found only where they are put), fitted to the Summoner (851's SK_S3_<set>)
- MaxItemsPerContainer 6; StartRoomItems the five sets (the great hall's containers, one each in turn)
- DefaultHero the Summoner; MenuLevel random_dungeonmagic_level5_select (826 with 5)
Args: none"""
import json, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
MAP = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
HJ = json.load(open(os.path.join(SA, "random_dungeon_magic5", "summoner_hero.json"), encoding="utf-8"))
AJ = json.load(open(os.path.join(SA, "summoner3", "armour.json"), encoding="utf-8"))
eal = unreal.EditorAssetLibrary; at = unreal.AssetToolsHelpers.get_asset_tools(); APE = unreal.AnimPoseExtensions
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# ---- her dungeon character
CHP = HJ["pawn"]
if not eal.does_asset_exist(CHP):
    f = unreal.BlueprintFactory(); f.set_editor_property("parent_class", unreal.load_asset("/Game/JRPG/Game/BP_JRPGSummoner3Character").generated_class())
    at.create_asset(CHP.split("/")[-1], CHP.rsplit("/", 1)[0], unreal.Blueprint, f)
chbp = unreal.load_asset(CHP); unreal.BlueprintEditorLibrary.compile_blueprint(chbp)
unreal.get_default_object(chbp.generated_class()).get_component_by_class(unreal.CapsuleComponent).set_editor_property("capsule_radius", 36.0)
unreal.BlueprintEditorLibrary.compile_blueprint(chbp); eal.save_loaded_asset(chbp, only_if_is_dirty=False)
# ---- her casts' release times
o = unreal.AnimPoseEvaluationOptions(); V = unreal.Vector
def release(anim):
    L_ = unreal.AnimationLibrary.get_sequence_length(anim); n = max(30, int(L_ * 60)); pts = []
    for k in range(n + 1):
        p = APE.get_anim_pose_at_time(anim, L_ * k / n, o)
        h = APE.get_bone_pose(p, "hand_r", unreal.AnimPoseSpaces.WORLD).translation; q = APE.get_bone_pose(p, "pelvis", unreal.AnimPoseSpaces.WORLD).translation
        pts.append(V(h.x - q.x, h.y - q.y, h.z - q.z))
    sp = [(pts[k + 1] - pts[k]).length() / (L_ / n) for k in range(n)]
    sm = [sum(sp[max(0, k - 2):k + 3]) / len(sp[max(0, k - 2):k + 3]) for k in range(n)]
    k = max(range(n), key=lambda i: sm[i]); return L_, L_ * (k + 0.5) / n
casts = []
for p in HJ["clips"]["casts"]:
    a = unreal.load_asset(p); assert a, p
    a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
    L_, hit = release(a); casts.append((a, hit, min(L_, hit + 0.42)))
flinch, death = unreal.load_asset(HJ["clips"]["flinch"]), unreal.load_asset(HJ["clips"]["death"])
for a in (flinch, death): a.set_editor_property("enable_root_motion", False); a.set_editor_property("force_root_lock", True); eal.save_loaded_asset(a, False)
# ---- the level
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): unreal.EditorLoadingAndSavingUtils.load_map(MAP)
w = ues.get_editor_world(); assert w.get_path_name().startswith(MAP + "."), w.get_path_name()
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
heroes = [h for h in gen.get_editor_property("heroes") if str(h.name) != HJ["name"]]
mage = next(h for h in heroes if str(h.name) == HJ["spells_like"])
h = unreal.RDHeroDef(); h.import_text(mage.export_text())
h.name = HJ["name"]; h.title = HJ["title"]; h.pawn_class = chbp.generated_class()
h.max_health = float(HJ["health"]); h.max_mana = float(HJ["mana"]); h.mana_per_second = float(HJ["mana_per_second"])
ws_ = []
for wd in h.weapons:
    wd.set_editor_property("attacks", [c[0] for c in casts]); wd.set_editor_property("attack_starts", [0.0] * len(casts))
    wd.set_editor_property("attack_ends", [float(c[2]) for c in casts]); wd.set_editor_property("hit_times", [float(c[1]) for c in casts])
    wd.set_editor_property("get_hit", flinch); wd.set_editor_property("death", death); ws_.append(wd)
h.weapons = ws_
h.abilities = HJ["abilities"]; h.armour = HJ["armour"]; h.starts_with = HJ["starts_with"]
h.accent = unreal.LinearColor(*HJ["accent"], 1.0)
keys = list(h.controls_keys); pad = list(h.controls_pad)
if HJ["keys_extra"] not in keys: keys.insert(max(len(keys) - 3, 0), HJ["keys_extra"])
if HJ["pad_extra"] not in pad: pad.insert(max(len(pad) - 3, 0), HJ["pad_extra"])
h.controls_keys = keys; h.controls_pad = pad
heroes.append(h)
gen.set_editor_property("heroes", heroes)
if HJ.get("default"): gen.set_editor_property("default_hero", HJ["name"])
# ---- the armour
items = [it for it in gen.get_editor_property("items") if it.kind != unreal.RDItemKind.ARMOUR]
for s in AJ["sets"]:
    it = unreal.RDItemDef(); it.name = s["title"]; it.kind = unreal.RDItemKind.ARMOUR; it.amount = float(s["armour"]); it.weight = 0.0
    it.icon = "armour_" + s["key"]; it.looks = s["looks"]
    fit = unreal.RDArmourFit(); fit.hero = HJ["name"]; m = unreal.load_asset(f"/Game/JRPG/Summoner3Armour/SK_S3_{s['key']}"); assert m, s["key"]
    fit.meshes = [m]; it.fits = [fit]; items.append(it)
gen.set_editor_property("items", items)
gen.set_editor_property("max_items_per_container", int(HJ["max_items_per_container"]))
gen.set_editor_property("start_room_items", [s["title"] for s in AJ["sets"]])
gen.set_editor_property("menu_level", MAP + "_select")
les.save_current_level()
back = gen.get_editor_property("heroes")
print("RDM5HEROES", MAP, "| heroes", [str(x.name) for x in back], "| default", gen.get_editor_property("default_hero"),
      "| her casts bolt at", [round(c[1], 2) for c in casts], "| items", len(gen.get_editor_property("items")),
      "| armour", [str(i.name) for i in gen.get_editor_property("items") if i.kind == unreal.RDItemKind.ARMOUR],
      "| up to", gen.get_editor_property("max_items_per_container"), "a container | menu", gen.get_editor_property("menu_level"),
      "| game mode", w.get_world_settings().get_editor_property("default_game_mode").get_name())
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
