"""README's tables for random_dungeonmagic_level5, written from the data the game is built from (so they say what it does):
- the heroes: SourceArt/random_dungeon_magic4/heroes.json (the Warrior, Mage, Warlock and Rogue: their cards, numbers,
  what they start with, the armour weights they wear) and random_dungeon_magic5/summoner_hero.json (the Summoner);
- the armour sets: SourceArt/summoner3/armour.json (the user's table: type, damage reduction and speed ratings, durability,
  tiers; the weight they give, the share of a blow taken off, the speed lost) and who wears each weight;
- the loot: SourceArt/random_dungeon_magic5/loot_table.json with level 4's items.json (potions and food by tier and rarity,
  the materials, the repair items) and the anvil's recipes;
- the weapons table: SourceArt/random_dungeon_magic5/weapons_table.json (type, speed and damage ratings, the damage and the
  attack's length they give, durability, rarity, tiers) and who wields each type.
Each table goes between its markers in README.md (<!-- rdm5:heroes -->, <!-- rdm5:armour -->, <!-- rdm5:weapons -->,
<!-- rdm5:loot -->, <!-- rdm5:recipes -->, each closed by <!-- /rdm5:... -->). Args: none (python 3, no other packages)"""
import json, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", ".."); SA = os.path.join(ROOT, "claude_ue5", "SourceArt")
HJ = json.load(open(os.path.join(SA, "random_dungeon_magic4", "heroes.json"), encoding="utf-8"))["heroes"]
SJ = json.load(open(os.path.join(SA, "random_dungeon_magic5", "summoner_hero.json"), encoding="utf-8"))
AJ = json.load(open(os.path.join(SA, "summoner3", "armour.json"), encoding="utf-8"))
WJ = json.load(open(os.path.join(SA, "random_dungeon_magic5", "weapons_table.json"), encoding="utf-8"))
LT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "loot_table.json"), encoding="utf-8"))
IJ = json.load(open(os.path.join(SA, "random_dungeon_magic4", "items.json"), encoding="utf-8"))["items"]
WHO = WJ["rules"]["who"]
HEROES = HJ + [dict(SJ, keys=None)]


def wears(h):
    w = [x for x in ("light", "medium", "heavy") if x in h.get("wears", [])]
    return "none" if not w else ("all: " if len(w) == 3 else "") + ", ".join(w)


def wields(name):
    w = WHO.get(name, [])
    return "all" if w == "all" else ("none" if not w else ", ".join(w))


def heroes_table():
    out = ["| Hero | Her card (what she can do) | Hit points | Mana (back a second) | Starts with | Wears armour | Wields from the weapons table |",
           "|---|---|---|---|---|---|---|"]
    for h in HEROES:
        mana = ("%d (%.1f)" % (h["mana"], h.get("mana_per_second", 0))) if h.get("mana") else "none"
        lvl = " (level 5 only)" if h["name"] == "Summoner" else ""
        out.append("| %s%s | %s | %d | %s | %s | %s | %s |" % (h["name"], lvl, "; ".join(h["abilities"]), h["health"], mana, h["starts_with"], wears(h), wields(h["name"])))
    return out


TYPES = ["full plate", "heavy", "medium", "light", "partial", "orc"]
def armour_table():
    out = ["| Set | Type | Damage reduction (1-10) | Speed (1-10) | Durability | Tier | Weight | A blow takes off | She moves | Worn by |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for s in sorted(AJ["sets"], key=lambda s: (TYPES.index(s["type"]), -s["damage_rating"], s["durability"])):
        by = [h["name"] for h in HEROES if s["weight"] in h.get("wears", [])]
        out.append("| %s | %s | %d | %d | %d | %s | %s | %d %% (%s %% worn out) | %s | %s |" % (
            s["title"], s["type"], s["damage_rating"], s["speed_rating"], s["durability"], ", ".join(str(t) for t in s["tiers"]), s["weight"],
            round(s["armour"] * 100), "%g" % round(s["armour"] * 50, 1), ("%d %% slower" % round(s["slower"] * 100)) if s["slower"] > 0 else "as fast", ", ".join(by) or "nobody"))
    return out


def loot_table():
    out = ["| Item | Kind | What it does | Tiers | Rarity |", "|---|---|---|---|---|"]
    T = LT["tiers"]
    def tiers(name):
        for k in ("Very Rare", "Legendary", "Wondrous", "Uncommon", "Small", "Medium", "Large", "Rare"):
            if name.startswith(k + " "): return T[k]
        return T.get(name, [])
    what = {"healing": lambda i: "%d %% of her hit points" % round(i["amount"] * 100), "mana": lambda i: "%d %% of her mana" % round(i["amount"] * 100),
            "speed": lambda i: "%d %% faster for %d s" % (round(i["amount"] * 100), i["seconds"]),
            "food": lambda i: "%d %% of her hit points a second for %d s" % (round(i["amount"] * 100), i["seconds"])}
    for i in IJ:
        out.append("| %s | %s | %s | %s | %d |" % (i["name"], i["kind"], what[i["kind"]](i), ", ".join(str(t) for t in tiers(i["name"])), i["rarity"]))
    for r in LT["repair"]["items"]:
        out.append("| %s | repair | mends %d %% of a set's or a found weapon's full durability | any | %d |" % (r["name"], round(r["repairs"] * 100), r["rarity"]))
    c = LT["components"]
    out.append("| %s | material | made into repair items at an anvil; 1 to %d at a time | any | %d each |" % (", ".join(c["items"]), c["found_max"], c["rarity"]))
    return out


def recipes_table():
    labels = []
    for r in LT["recipes"]["items"]:
        for k in r["takes"]:
            if k not in labels: labels.append(k)
    out = ["| Repair item (mends) | " + " | ".join(labels) + " |", "|---|" + "---|" * len(labels)]
    rep = {r["name"]: r["repairs"] for r in LT["repair"]["items"]}
    for r in LT["recipes"]["items"]:
        out.append("| %s (%d %%) | " % (r["name"], round(rep[r["name"]] * 100)) + " | ".join(str(r["takes"].get(k, "")) for k in labels) + " |")
    return out


def weapons_table():
    out = ["| Weapon | Type | Speed (1-10) | Damage (1-10) | Damage a hit | An attack every | Durability | Rarity | Tiers | Wielded by |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for w in sorted(WJ["weapons"], key=lambda w: (min(w["tiers"]), w["type"], w["name"])):
        t = w["type"]; who = [n for n, x in WHO.items() if x == "all" or (isinstance(x, list) and (t in x or (t == "ranged" and "ranged" in x)))]
        out.append("| %s | %s | %d | %d | %d | %.2f s | %d | %d | %s | %s |" % (w["name"], t, w["speed"], w["damage"], 8 + 3 * w["damage"], 1.6 - (w["speed"] - 1) * 1.05 / 9.0,
                                                                               w["durability"], w["rarity"], ", ".join(str(x) for x in w["tiers"]), ", ".join(who) or "nobody"))
    return out


p = os.path.join(ROOT, "README.md"); s = open(p, encoding="utf-8").read()
for key, rows in (("heroes", heroes_table()), ("armour", armour_table()), ("weapons", weapons_table()), ("loot", loot_table()), ("recipes", recipes_table())):
    a, b = "<!-- rdm5:%s -->" % key, "<!-- /rdm5:%s -->" % key
    assert s.count(a) == 1 and s.count(b) == 1, key
    s = re.sub(re.escape(a) + r".*?" + re.escape(b), lambda m: a + "\n" + "\n".join(rows) + "\n" + b, s, flags=re.S)
    print("rdm5_tables_doc: %s, %d rows" % (key, len(rows) - 2))
open(p, "w", encoding="utf-8", newline="").write(s)
