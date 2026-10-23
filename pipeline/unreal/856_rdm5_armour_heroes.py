"""random_dungeonmagic_level5: who wears what. Each armour set has a weight (SourceArt/summoner3/armour.json: light, medium or
heavy) and each hero wears only some weights ("wears": SourceArt/random_dungeon_magic4/heroes.json for the Warrior, Mage,
Warlock and Rogue; random_dungeon_magic5/summoner_hero.json for the Summoner):
  Warrior: light, medium and heavy        Warlock: light and medium        Rogue: light        Mage: none
  Summoner: light, medium and heavy (every set was made for her: 849-851)
A set is worn by a hero only when it is of a weight she wears and a fit was made for her: the Summoner's are 851's
(/Game/JRPG/Summoner3Armour/SK_S3_<set>); the other heroes' are 849 heroes + summoner3_armour.py --hero + 851 <mesh>
(/Game/JRPG/HeroArmour/<mesh>/SK_<mesh>_<set>; the Warrior is Fem5, the Warlock DarkCaster, the Rogue Rogue).
Sets the game: each armour item's ArmourWeight and Fits (random_dungeonmagic_level5), and every hero's Wears, Abilities and
Armour line (the card) on random_dungeonmagic_level5 and level4 and their menus (_select): the four heroes' text from
heroes.json, so that the card says what the game does. Run after 852 (level 5's heroes and items) and 826 (the menus).
Leaves the editor on random_dungeonmagic_level5. Args: none"""
import json, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
AJ = json.load(open(os.path.join(SA, "summoner3", "armour.json"), encoding="utf-8"))
HJ = {h["name"]: h for h in json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"]}
SJ = json.load(open(os.path.join(SA, "random_dungeon_magic5", "summoner_hero.json"), encoding="utf-8"))
MESH = {"Warrior": "Fem5", "Mage": "Caster", "Warlock": "DarkCaster", "Rogue": "Rogue", "Summoner": "Summoner3"}
WEIGHT = {"light": unreal.RDArmourWeight.LIGHT, "medium": unreal.RDArmourWeight.MEDIUM, "heavy": unreal.RDArmourWeight.HEAVY}
WEARS = {n: h.get("wears", []) for n, h in HJ.items()}; WEARS["Summoner"] = SJ["wears"]
eal = unreal.EditorAssetLibrary; les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
M = "/Game/RandomDungeon/Maps/"


def fit_mesh(hero, key):
    m = MESH.get(hero)
    p = f"/Game/JRPG/Summoner3Armour/SK_S3_{key}" if m == "Summoner3" else f"/Game/JRPG/HeroArmour/{m}/SK_{m}_{key}"
    return unreal.load_asset(p) if eal.does_asset_exist(p) else None


def heroes_fixed(heroes):
    """the heroes with their Wears and card lines as the data says (made fresh: nothing kept from another level)"""
    out = []
    for h in heroes:
        n = str(h.name)
        h.wears = [WEIGHT[w] for w in WEARS.get(n, [])]
        if n in HJ:
            h.abilities = HJ[n]["abilities"]; h.armour = HJ[n]["armour"]
        out.append(h)
    return out


report = {}
for lv in ("random_dungeonmagic_level5", "random_dungeonmagic_level5_select", "random_dungeonmagic_level4", "random_dungeonmagic_level4_select"):
    unreal.EditorLoadingAndSavingUtils.load_map(M + lv)
    acts = eas.get_all_level_actors()
    gen = next((a for a in acts if isinstance(a, unreal.RDDungeonGenerator)), None)
    sel = next((a for a in acts if isinstance(a, unreal.RDHeroSelect)), None)
    owner = gen or sel
    owner.set_editor_property("heroes", heroes_fixed(list(owner.get_editor_property("heroes"))))
    if gen is not None and lv == "random_dungeonmagic_level5":
        items = []; fits_made = {}
        for it in gen.get_editor_property("items"):
            if it.kind == unreal.RDItemKind.ARMOUR:
                s = next(x for x in AJ["sets"] if x["title"] == str(it.name))
                it.armour_weight = WEIGHT[s["weight"]]
                fits = []
                for hero, ws in WEARS.items():
                    if s["weight"] not in ws: continue
                    m = fit_mesh(hero, s["key"])
                    if m is None: print("856: no fit of", s["key"], "for", hero); continue
                    f = unreal.RDArmourFit(); f.hero = hero; f.meshes = [m]; fits.append(f)
                it.fits = fits; fits_made[s["key"]] = [str(f.hero) for f in fits]
            items.append(it)
        gen.set_editor_property("items", items)
        report["fits"] = fits_made
    les.save_current_level()
    back = owner.get_editor_property("heroes")
    report[lv] = {str(h.name): [str(w.name).lower() for w in h.wears] for h in back}
unreal.EditorLoadingAndSavingUtils.load_map(M + "random_dungeonmagic_level5")
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
report["read back"] = {str(i.name): [str(i.armour_weight.name).lower(), [str(f.hero) for f in i.fits]] for i in gen.get_editor_property("items") if i.kind == unreal.RDItemKind.ARMOUR}
print("RDM5ARMOUR", json.dumps(report, ensure_ascii=False))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
