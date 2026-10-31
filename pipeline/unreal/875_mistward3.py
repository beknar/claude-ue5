"""mistward_castle: the user's list of 2026-10-30 (docs/improvements3.txt), its rules (the Summoner is 876, the pictures 877).
Reads SourceArt/mistward/harvest.json (the user's tables) and writes into the castle's generator (the "Mistward3" switches,
RD/RDMistward3.cpp):
- harvests (bHarvest): the essences, the families' parts and the any-tier materials a dead monster leaves floating over it,
  their chances, a boss's / usurper's / arena's more, the piles' tints by tier
- items: the five essences and six parts (kind Component, found only on the dead: weight 0), a scroll for each of the
  table's 30 spells ("Scroll of <spell>", kind Scroll, its tier the spell's, its picture by the spell's type), rings broken
  down by the type "ring"
- recipes (bRecipeTiers: the anvil offers one once its tier is open; a scroll's only to a hero who reads its type): the
  16 potions and the 30 scrolls; Wood Glue in some of the old recipes (the list: it was found but nothing used it)
- the breakdowns of rings and the torch (bBreakAnyGear: "any piece of equipment can be broken down at an anvil")
- the heroes who read scrolls (ScrollTypes: the Mage all four types, the Warlock offense and curses; the Summoner's in 876)
- the fires' crackle: Env.Torch / Env.Brazier / Env.Hearth at sounds.json's volume x 0.2 (half the reel's x 0.4)
Idempotent: what it made before is taken out by name and kind and made again. Saves the map (play stopped). Args: none"""
import json, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
HV = json.load(open(os.path.join(SA, "mistward", "harvest.json"), encoding="utf-8"))
LT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "loot_table.json"), encoding="utf-8"))
SJ = json.load(open(os.path.join(SA, "random_dungeon_combat", "sounds.json"), encoding="utf-8"))
MAP = "/Game/RandomDungeon/Maps/mistward_castle"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not ues.get_editor_world().get_path_name().startswith(MAP + "."): les.load_level(MAP)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
TYPE = {"Offense": unreal.RDSpellType.OFFENSE, "Protection": unreal.RDSpellType.PROTECTION, "Curse": unreal.RDSpellType.CURSE, "Summon": unreal.RDSpellType.SUMMON}
TNAME = {v: k for k, v in TYPE.items()}
scroll_of = lambda spell: f"Scroll of {spell}"

# ---- harvests
gen.set_editor_property("harvest", True)
gen.set_editor_property("essences", [unreal.Name(n) for n in HV["essences"]]); gen.set_editor_property("essence_own_tier", float(HV["own_tier"]))
parts = []
for p in HV["parts"]:
    hp = unreal.RDHarvestPart(); hp.family = p["family"]; hp.part = p["part"]; hp.tiers = p["tiers"]; parts.append(hp)
gen.set_editor_property("harvest_parts", parts); gen.set_editor_property("harvest_part_chance", float(HV["part_chance"]))
gen.set_editor_property("harvest_any", [unreal.Name(n) for n in HV["any"]]); gen.set_editor_property("harvest_any_chance", float(HV["any_chance"]))
gen.set_editor_property("boss_essences", int(HV["boss_essences"])); gen.set_editor_property("boss_parts", int(HV["boss_parts"]))
gen.set_editor_property("harvest_tints", [unreal.LinearColor(*c, 1.0) for c in HV["tints"]])

# ---- items
new_parts = HV["essences"] + [p["part"] for p in HV["parts"]]
items = [i for i in gen.get_editor_property("items") if str(i.name) not in new_parts and i.kind != unreal.RDItemKind.SCROLL]
have = {str(i.name) for i in items}
for n in HV["any"]: assert n in have, f"875: the material {n} is not among the castle's items"
for n in HV["potions"]: assert n in have, f"875: the potion {n} is not among the castle's items"
for k, n in enumerate(HV["essences"]):
    it = unreal.RDItemDef(); it.name = n; it.kind = unreal.RDItemKind.COMPONENT; it.weight = 0.0; it.found_max = 1
    it.icon = unreal.Name(HV["icons"][n]); it.looks = f"an essence harvested from the dead of tier {k + 1} and above"; items.append(it)
for p in HV["parts"]:
    n = p["part"]
    it = unreal.RDItemDef(); it.name = n; it.kind = unreal.RDItemKind.COMPONENT; it.weight = 0.0; it.found_max = 1
    it.icon = unreal.Name(HV["icons"][n]); it.looks = f"harvested from the {p['family'].lower()} kind (tiers {', '.join(map(str, p['tiers']))})"; items.append(it)
spells = [s for s in gen.get_editor_property("spells") if s.number <= 100]          # (the table's 30: the chi attacks are 101 on)
assert len(spells) == 30, f"875: {len(spells)} spells of the table"
for s in spells:
    it = unreal.RDItemDef(); it.name = scroll_of(str(s.name)); it.kind = unreal.RDItemKind.SCROLL; it.spell = s.name
    it.weight = 0.0; it.found_max = 1; it.tiers = [int(s.tier)]; it.icon = unreal.Name(HV["scroll_icons"][TNAME[s.type]])
    it.looks = f"a scroll of {s.name}: cast once at no mana"; items.append(it)
for it in items:
    if it.kind == unreal.RDItemKind.RING: it.weapon_type = "ring"
gen.set_editor_property("items", items)

# ---- recipes
def part(label, kinds, n):
    p = unreal.RDRecipePart(); p.label = label; p.any_of = [unreal.Name(k) for k in kinds]; p.count = int(n); return p
scrolls = {scroll_of(str(s.name)) for s in spells}
recipes = [r for r in gen.get_editor_property("recipes") if str(r.item) not in HV["potions"] and str(r.item) not in scrolls]
for r in recipes:
    # (Wood Glue in the repair items' and the torch's: taken out and put in again, never twice)
    if str(r.item) in HV["wood_glue"]:
        r.parts = [p for p in r.parts if str(p.label) != "wood glue"] + [part("wood glue", ["Wood Glue"], HV["wood_glue"][str(r.item)])]
item_tier = {str(i.name): (min(i.tiers) if len(i.tiers) else 0) for i in items}
for n, takes in HV["potions"].items():
    rc = unreal.RDRecipe(); rc.item = n; rc.tier = item_tier[n]; rc.parts = [part(k.lower(), [k], c) for k, c in takes.items()]; recipes.append(rc)
made = {"Offense": 0, "Protection": 0, "Curse": 0, "Summon": 0}
for s in spells:
    t = str(int(s.tier)); ty = TNAME[s.type]
    ess, ne = HV["scroll_essences"][t]; ne = HV["scroll_essence_override"].get(str(s.name), ne)
    pn = HV["scroll_part_of"][ty][t]
    rc = unreal.RDRecipe(); rc.item = scroll_of(str(s.name)); rc.tier = int(s.tier)
    rc.parts = [part(ess.lower(), [ess], ne), part(pn.lower(), [pn], HV["scroll_parts"][t])]; recipes.append(rc); made[ty] += 1
gen.set_editor_property("recipes", recipes)
gen.set_editor_property("recipe_tiers", True)

# ---- rings and the torch broken down
bds = [b for b in gen.get_editor_property("breakdowns") if not any(str(t) in HV["gear_breakdown"] for t in b.types)]
for ty, gives in HV["gear_breakdown"].items():
    b = unreal.RDBreakdown(); b.types = [ty]; b.gives = [unreal.Name(k) for k in gives]; b.per_tier = list(gives.values()); bds.append(b)
gen.set_editor_property("breakdowns", bds)
gen.set_editor_property("break_any_gear", True)

# ---- who reads scrolls (the Summoner's own in 876)
heroes = list(gen.get_editor_property("heroes"))
for h in heroes:
    h.scroll_types = [TYPE[t] for t in HV["scroll_readers"].get(str(h.name), [])]
gen.set_editor_property("heroes", heroes)

# ---- the fires' crackle (sounds.json's volume x fire_scale: absolute, so running it again changes nothing)
sets = SJ.get("sets", SJ); snd = gen.get_editor_property("sounds"); fires = {}
for k in ("Env.Torch", "Env.Brazier", "Env.Hearth"):
    if k not in snd: continue
    st = snd[k]; before = round(st.volume, 3); st.volume = float(sets[k]["volume"]) * float(HV["fire_scale"]); snd[k] = st; fires[k] = (before, round(st.volume, 3))
gen.set_editor_property("sounds", snd)

gen.modify(); les.save_current_level()
back = gen.get_editor_property("recipes")
print(f"875 mistward_castle: harvest {gen.get_editor_property('harvest')} | essences {len(gen.get_editor_property('essences'))}, parts {len(gen.get_editor_property('harvest_parts'))}, "
      f"any {len(gen.get_editor_property('harvest_any'))} | items {len(gen.get_editor_property('items'))} (scrolls {sum(1 for i in gen.get_editor_property('items') if i.kind == unreal.RDItemKind.SCROLL)}) | "
      f"recipes {len(back)}: potions {sum(1 for r in back if str(r.item) in HV['potions'])}, scrolls {made} | tiers {sorted({int(r.tier) for r in back})} | "
      f"wood glue in {[str(r.item) for r in back if any(str(p.label) == 'wood glue' for p in r.parts)]} | breakdowns {[list(map(str, b.types)) for b in gen.get_editor_property('breakdowns') if any(str(t) in HV['gear_breakdown'] for t in b.types)]} | "
      f"readers {[(str(h.name), [TNAME[t] for t in h.scroll_types]) for h in gen.get_editor_property('heroes') if len(h.scroll_types)]} | fires {fires}")
import gc
del gen, items, recipes, heroes, spells, back, snd
gc.collect()
