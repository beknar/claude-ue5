"""random_dungeonmagic_level5's armour table, loot table and crafting (the user's tables of 2026-10-23), and the fires'
volume on every dungeon level.
Run after 849-851 for the 27 armour sets (summoner3/armour.json; fitted to every hero who wears each set's weight:
`849_rdm5_armour_export.py sets <key...>`, `summoner3_armour.py [--hero <mesh>] [--pct N] [--legs 60]`, `851 <mesh> <keys>`),
after 852 / 855 (the level's heroes and weapons) and before 830 --level 5 (the pictures).
- the fires: sounds.json's Env.Torch / Env.Brazier / Env.Hearth volumes (now x 0.4: the user found the crackle too loud)
  written into the Sounds table of every dungeon level that has one (only those three sets' Volume: 797 would rewrite the
  whole table, and level 4 and 5 add sets of their own with 825)
- random_dungeonmagic_level5's Items, rebuilt:
    the 27 armour sets (kind Armour): Amount the damage reduction rating x 5 % (half that once its durability is 0),
      Slower (10 - the speed rating) x 3 %, Durability, the ratings and type for the inventory, Weight its rarity (20),
      Tiers, its weight (light / medium / heavy, by type: armour.json's _weights) and a fit for every hero who wears that
      weight (the Summoner's SK_S3_<set>, the others' /Game/JRPG/HeroArmour/<mesh>/SK_<mesh>_<set>)
    the potions and foods (level 4's) with the tiers of loot_table.json
    the 15 crafting materials (kind Component, rarity 25, 1 to 3 at a time, every tier) and the 5 repair items (kind
      Repair, Amount the share of a full durability they give back, their rarity, every tier)
    the weapons (855's) as they are
- Recipes (loot_table.json: what an anvil makes of what), bAnvilEverySection (an anvil in every set of rooms: a forge's,
  an armory's, else one placed in its largest room, the great hall in the start section), StartRoomItems the tier-1 sets
- the start section built again (its great hall's anvil is part of its saved furniture)
Prints the items by kind and tier, the recipes, the anvils of the start section. Saves the levels; ends on level 5.
Args: none"""
import json, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
AJ = json.load(open(os.path.join(SA, "summoner3", "armour.json"), encoding="utf-8"))
LT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "loot_table.json"), encoding="utf-8"))
SJ = json.load(open(os.path.join(SA, "random_dungeon_combat", "sounds.json"), encoding="utf-8"))
HJ = {h["name"]: h for h in json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"]}
SUM = json.load(open(os.path.join(SA, "random_dungeon_magic5", "summoner_hero.json"), encoding="utf-8"))
MAPS = "/Game/RandomDungeon/Maps/"
LEVEL = MAPS + "random_dungeonmagic_level5"
MESH = {"Warrior": "Warrior3", "Mage": "Caster", "Warlock": "DarkCaster", "Rogue": "Rogue", "Summoner": "Summoner3"}
WEARS = {n: h.get("wears", []) for n, h in HJ.items()}; WEARS["Summoner"] = SUM["wears"]
WEIGHT = {"light": unreal.RDArmourWeight.LIGHT, "medium": unreal.RDArmourWeight.MEDIUM, "heavy": unreal.RDArmourWeight.HEAVY}
eal = unreal.EditorAssetLibrary; les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
snake = lambda s: "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")


def load(level):
    if not ues.get_editor_world().get_path_name().startswith(level + "."): unreal.EditorLoadingAndSavingUtils.load_map(level)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(level + "."), w.get_path_name()
    return next((a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator)), None)


# ---- the fires, on every dungeon level with a Sounds table
def fire_volumes():
    sets = SJ.get("sets", SJ)
    return {k: float(sets[k]["volume"]) for k in ("Env.Torch", "Env.Brazier", "Env.Hearth")}
FV = fire_volumes()
report = {"fires": {}}
for lv in ("random_dungeoncombat_level", "random_dungeonmagic_level", "random_dungeonmagic_level2", "random_dungeonmagic_level3",
           "random_dungeonmagic_level4", "random_dungeonmagic_level5"):
    g = load(MAPS + lv)
    if g is None: continue
    snd = g.get_editor_property("sounds"); done = {}
    for k, v in FV.items():
        if k not in snd: continue
        st = snd[k]; before = round(st.volume, 3); st.volume = v; snd[k] = st; done[k] = (before, v)
    if done:
        g.modify(); g.set_editor_property("sounds", snd); les.save_current_level()
        back = g.get_editor_property("sounds")
        report["fires"][lv] = {k: [b, round(back[k].volume, 3)] for k, (b, v) in done.items()}

# ---- level 5's items
gen = load(LEVEL)
old = list(gen.get_editor_property("items"))
by = {str(i.name): i for i in old}
items = []
tiers = LT["tiers"]


def tier_of(name):
    for k, t in tiers.items():
        if k.startswith("_"): continue
        if name == k or name.startswith(k + " "): return list(t)
    return []


# potions and food (level 4's, now with tiers): the rank its name starts with ("Very Rare X" does not start with "Rare ")
for i in old:
    if i.kind in (unreal.RDItemKind.HEALING, unreal.RDItemKind.MANA, unreal.RDItemKind.SPEED, unreal.RDItemKind.FOOD):
        n = str(i.name)
        t = tier_of(n)
        assert t, "no tier for " + n
        i.tiers = t; items.append(i)
# weapons (855's) as they are
items += [i for i in old if i.kind == unreal.RDItemKind.WEAPON]
# the armour sets
fits_made = {}
for s in AJ["sets"]:
    it = unreal.RDItemDef(); it.name = s["title"]; it.kind = unreal.RDItemKind.ARMOUR
    it.amount = float(s["armour"]); it.slower = float(s["slower"]); it.durability = float(s["durability"])
    it.damage_rating = int(s["damage_rating"]); it.speed_rating = int(s["speed_rating"]); it.armour_type = s["type"]
    it.weight = float(s["rarity"]); it.tiers = list(s["tiers"]); it.icon = "armour_" + s["key"]; it.looks = s["looks"]
    it.armour_weight = WEIGHT[s["weight"]]; it.found_max = 1
    fits = []
    for hero, ws in WEARS.items():
        if s["weight"] not in ws: continue
        m = MESH[hero]
        p = f"/Game/JRPG/Summoner3Armour/SK_S3_{s['key']}" if m == "Summoner3" else f"/Game/JRPG/HeroArmour/{m}/SK_{m}_{s['key']}"
        mesh = unreal.load_asset(p) if eal.does_asset_exist(p) else None
        if mesh is None: print("857: no fit of", s["key"], "for", hero); continue
        f = unreal.RDArmourFit(); f.hero = hero; f.meshes = [mesh]; fits.append(f)
    it.fits = fits; fits_made[s["key"]] = [str(f.hero) for f in fits]
    items.append(it)
# the crafting materials and the repair items
C = LT["components"]
for n in C["items"]:
    it = unreal.RDItemDef(); it.name = n; it.kind = unreal.RDItemKind.COMPONENT; it.amount = 0.0; it.weight = float(C["rarity"])
    it.found_max = int(C["found_max"]); it.icon = "comp_" + snake(n); it.tiers = []; items.append(it)
for r in LT["repair"]["items"]:
    it = unreal.RDItemDef(); it.name = r["name"]; it.kind = unreal.RDItemKind.REPAIR; it.amount = float(r["repairs"]); it.weight = float(r["rarity"])
    it.found_max = 1; it.icon = "rep_" + snake(r["name"]); it.tiers = []; items.append(it)
gen.set_editor_property("items", items)
# ---- the recipes
G = LT["recipes"]["groups"]; recipes = []
for r in LT["recipes"]["items"]:
    rc = unreal.RDRecipe(); rc.item = r["name"]; parts = []
    for label, count in r["takes"].items():
        pt = unreal.RDRecipePart(); pt.label = label; pt.any_of = list(G[label]); pt.count = int(count); parts.append(pt)
    rc.parts = parts; recipes.append(rc)
gen.set_editor_property("recipes", recipes)
gen.set_editor_property("anvil_every_section", True)
gen.set_editor_property("start_room_items", list(LT["start_room_armour"]["items"]))
# ---- the start section again (its great hall gets its anvil as saved furniture)
gen.modify(); gen.build_start_section()
les.save_current_level()
sec = gen.get_section(unreal.IntPoint(0, 0))
back = gen.get_editor_property("items")
count = {}
for i in back: count.setdefault(str(i.kind.name).lower(), 0); count[str(i.kind.name).lower()] += 1
report["items"] = count
report["tiers"] = {str(i.name): list(i.tiers) for i in back if i.kind != unreal.RDItemKind.WEAPON and i.kind != unreal.RDItemKind.ARMOUR and len(i.tiers)}
report["armour"] = {str(i.name): [round(i.amount, 2), round(i.slower, 2), int(i.durability), list(i.tiers), str(i.armour_weight.name).lower(), [str(f.hero) for f in i.fits]] for i in back if i.kind == unreal.RDItemKind.ARMOUR}
report["recipes"] = {str(r.item): {str(p.label): int(p.count) for p in r.parts} for r in gen.get_editor_property("recipes")}
report["start anvils"] = [[round(v.x), round(v.y), round(v.z)] for v in sec.get_anvil_points()] if sec else None
report["start room items"] = [str(x) for x in gen.get_editor_property("start_room_items")]
print("RDM5LOOT", json.dumps(report, ensure_ascii=False))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
