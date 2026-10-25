"""README's tables for random_dungeonmagic_level5, written from the data the game is built from (so they say what it does):
- the heroes: SourceArt/random_dungeon_magic4/heroes.json (the Warrior, Mage, Warlock and Rogue: their cards, numbers,
  what they start with, the armour weights they wear) and random_dungeon_magic5/summoner_hero.json (the Summoner);
- the armour sets: SourceArt/summoner3/armour.json (the user's table: type, damage reduction and speed ratings, durability,
  tiers; the weight they give, the share of a blow taken off, the speed lost) and who wears each weight;
- the loot: SourceArt/random_dungeon_magic5/loot_table.json with level 4's items.json (potions and food by tier and rarity,
  the materials, the repair items) and the anvil's recipes;
- the weapons table: SourceArt/random_dungeon_magic5/weapons_table.json (type, speed and damage ratings, the damage and the
  attack's length they give, durability, rarity, tiers) and who wields each type;
- the spell table: SourceArt/random_dungeon_magic5/spells.json (the user's 30 spells: type, effect, drop chance, mana,
  cooldown, duration; the tier of its tome, what it does in the game, who learns it);
- the rings and the weapons broken down at an anvil: loot_table.json's rings and breakdown;
- the monsters by tier: SourceArt/random_dungeon_magic5/monster_tiers.json (the gallery's monsters of each tier, the tier's
  hit points, damage, speed, blows' pace and abilities).
Each table goes between its markers in README.md (<!-- rdm5:heroes -->, <!-- rdm5:armour -->, <!-- rdm5:weapons -->,
<!-- rdm5:loot -->, <!-- rdm5:recipes -->, <!-- rdm5:spells -->, <!-- rdm5:rings -->, <!-- rdm5:breakdown -->,
<!-- rdm5:monsters -->, each closed by <!-- /rdm5:... -->). Args: none (python 3, no other packages)"""
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


SP = json.load(open(os.path.join(SA, "random_dungeon_magic5", "spells.json"), encoding="utf-8"))
MT = json.load(open(os.path.join(SA, "random_dungeon_magic5", "monster_tiers.json"), encoding="utf-8"))
def tier_of_mana(m): return 1 if m <= 15 else 2 if m <= 30 else 3 if m <= 60 else 4 if m <= 110 else 5
KIND = {"Bolt": "a bolt", "Lash": "an arc before her", "Ward": "a shield on her", "Skin": "armour on her", "Dispel": "cleanses her", "Drain": "a channel",
        "Cloud": "an area that lingers", "Veil": "on her", "Curse": "an area", "Raise": "corpses rise", "Rune": "a zone at her feet", "Nova": "a ring round her",
        "Mirror": "on her", "Rend": "the one she faces", "Corpse": "corpses burst", "Pillar": "a column, burning ground", "Rift": "a rift that pulls",
        "Pact": "on her", "Knight": "a champion", "Meteors": "a storm of strikes", "Sanctum": "a zone at her feet", "Apocalypse": "every monster in sight"}
def what_spell(s):
    k = s["kind"]; d = s.get("damage", 0); per = s.get("per_second") and s["duration"] > 0
    dmg = ("%g a second" % round(d / s["duration"], 1)) if per else ("%d" % d if d else "")
    bits = []
    if dmg: bits.append(dmg + " damage" + (" each" if k in ("Meteors", "Corpse") else ""))
    if s.get("burn"): bits.append("then %d %% more over %d s, %d %% of it back to her" % (round(s["burn"] * 100), s["duration"], round(s.get("drain", 0) * 100)))
    if s.get("pierce"): bits.append("passes through")
    if s.get("slow"): bits.append("slows %d %%" % round(s["slow"] * 100))
    if k == "Bolt" and s.get("count"): bits.append("jumps %d times within %g m" % (s["count"], s["radius"] / 100.0))
    if k == "Bolt" and s.get("radius") and not s.get("count"): bits.append("all of it within %g m" % (s["radius"] / 100.0))
    if k == "Ward": bits.append(("takes %d %% of her hit points" % round(s["amount"] * 100)) if s.get("amount") else "takes %d blows whole" % s["count"])
    if k == "Skin": bits.append("armour +%d %%" % round(s["amount"] * 100))
    if k == "Lash": bits.append("pushes %g m" % (s["amount"] / 100.0))
    if k == "Drain": bits.append("%d %% back to her" % round(s["drain"] * 100))
    if k == "Veil": bits.append("monsters lose her; %d %% of blows miss" % round(s["amount"] * 100))
    if k == "Curse": bits.append("they take %d %% more, deal %d %% less" % (round(s["amount"] * 100), round(s["amount"] * 100)))
    if k == "Raise": bits.append("up to %d, %d %% of their hit points" % (s["count"], round(s["amount"] * 100)))
    if k == "Rune": bits.append("blows on her %d %% less inside" % round(s["amount"] * 100))
    if k == "Nova": bits.append("costs %d %% of her hit points" % round(s["amount"] * 100))
    if k == "Mirror": bits.append("blows turned back on the attacker")
    if k == "Pact": bits.append("a killing blow leaves her %d %% of her hit points, once" % round(s["amount"] * 100))
    if k == "Knight": bits.append("the %s on her side (%d %% of a tier-5 monster)" % (SP["knight"]["monster"], round(SP["knight"]["strength"] * 100)))
    if k == "Meteors": bits.append("%d strikes within %g m" % (s["count"], s["radius"] / 100.0))
    if k == "Sanctum": bits.append("no blow hurts her inside")
    if s.get("radius") and k in ("Cloud", "Curse", "Nova", "Rune", "Sanctum", "Rift", "Pillar", "Corpse"): bits.append("%g m round" % (s["radius"] / 100.0))
    return "%s: %s" % (KIND[k], ", ".join(bits))
def spells_table():
    who = {t: [h for h, ts in SP["learns"].items() if t in ts] for t in ("Offense", "Protection", "Curse", "Summon")}
    out = ["| # | Spell | Type | The table's effect | Drop chance | Mana | Cooldown | Duration | Tier of its tome | In the game | Learned by |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in SP["spells"]:
        out.append("| %d | %s | %s | %s | %.2f %% | %d | %s | %s | %d | %s | %s |" % (s["n"], s["name"], s["type"], s["effect"], s["drop"], s["mana"],
                   ("%d s" % s["cooldown"]) if s["cooldown"] else "none", ("%d s" % s["duration"]) if s["duration"] else "instant", tier_of_mana(s["mana"]),
                   what_spell(s), ", ".join(who[s["type"]]) or "nobody"))
    return out
def rings_table():
    R = LT["rings"]; out = ["| Ring | Kind | While worn | Tiers | Rarity | Worn by |", "|---|---|---|---|---|---|"]
    what = {"Magic": "mana", "Health": "hit points", "Dexterity": "ranged weapons' damage"}
    for k in R["kinds"]:
        for n in range(1, 11):
            out.append("| %s %d | %s | +%d %% %s | %d | %d | %s |" % (k["name"], n, k["kind"].lower(), n * 10, what[k["kind"]], (n + 1) // 2, R["rarity"], ", ".join(k["who"])))
    return out
def breakdown_table():
    out = ["| Weapon types | An anvil breaks one into (a tier-1 weapon; x its tier) |", "|---|---|"]
    for b in LT["breakdown"]["types"]:
        out.append("| %s | %s |" % (", ".join(b["types"]), ", ".join("%d %s" % (v, k) for k, v in b["gives"].items())))
    return out
def monsters_table():
    T = MT["tiers"]; out = ["| Tier | Hit points / damage (x her reference: 100 / 25) | Speed | A blow every | Abilities' strength | Monsters (gallery rank; ability) |",
                            "|---|---|---|---|---|---|"]
    for t in range(1, 6):
        ms = [m for m in MT["monsters"] if m["tier"] == t]
        out.append("| %d | %d / %g | x %g | x %g | %s | %s |" % (t, round(100 * T["health"][t - 1]), round(25 * T["damage"][t - 1], 1), T["speed"][t - 1], T["attack_interval"][t - 1],
                   ("x %g" % T["ability"][t - 1]) if T["ability"][t - 1] else "none",
                   ", ".join("%s (%d%s)" % (m["name"], m["rank"], "" if m["ability"] == "None" else "; " + m["ability"].lower()) for m in ms)))
    return out


p = os.path.join(ROOT, "README.md"); s = open(p, encoding="utf-8").read()
for key, rows in (("heroes", heroes_table()), ("armour", armour_table()), ("weapons", weapons_table()), ("loot", loot_table()), ("recipes", recipes_table()),
                  ("spells", spells_table()), ("rings", rings_table()), ("breakdown", breakdown_table()), ("monsters", monsters_table())):
    a, b = "<!-- rdm5:%s -->" % key, "<!-- /rdm5:%s -->" % key
    assert s.count(a) == 1 and s.count(b) == 1, key
    s = re.sub(re.escape(a) + r".*?" + re.escape(b), lambda m: a + "\n" + "\n".join(rows) + "\n" + b, s, flags=re.S)
    print("rdm5_tables_doc: %s, %d rows" % (key, len(rows) - 2))
open(p, "w", encoding="utf-8", newline="").write(s)
