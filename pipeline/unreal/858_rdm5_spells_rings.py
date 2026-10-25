"""random_dungeonmagic_level5: the spell table, rings, spell tomes, found weapons broken down at anvils, the containers'
chance, corpses that stay and the Escape menu (the user's of 2026-10-24). Run after 857 (the items) and 855 (the weapons),
before 830 --level 5 (the pictures).
- Spells: SourceArt/random_dungeon_magic5/spells.json (the 30 of the table: kind, mana, cooldown, duration, drop chance,
  tier by mana, damage, effects from MagicProjectilesVol4 / 5, ToonExplosionVol1 / ToonExplosionsVol2, StylizedShieldsVol1)
- Items (the previous rings and tomes removed first):
    30 rings (loot_table.json's rings: 3 kinds of 10, Amount 0.1 to 1.0, tiers 1-5 by twos, rarity 25)
    a Spell Tome (rarity 25, every tier: the spell is picked when the container is filled) and a "Tome of <spell>" for each
      spell (rarity 0: only what a Spell Tome becomes; the spell's tier)
    the weapons' types for breaking them down (the table's, a ranged one a bow or a crossbow by its name)
- Breakdowns (loot_table.json's breakdown), ContainerLootChance 0.33, bKeepCorpses, bEscapeMenu, the Knight's monster
- the heroes: Learns (spells.json's learns), RingKinds (who wears each ring kind); their own spells (Fire, Dark Fire) become
  the table's Fire Bolt and Dark Fire (their effects and what they do; their mana and damage stay the cards')
- the editor's key to stop play moved from Escape to Shift+Escape (Escape opens the game's menu in play-in-editor too)
Prints the spells by tier, the rings and tomes, the heroes' learns. Saves the level. Args: none"""
import json, os, unreal
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic5"
SP = json.load(open(os.path.join(SA, "spells.json"), encoding="utf-8"))
LT = json.load(open(os.path.join(SA, "loot_table.json"), encoding="utf-8"))
WT = json.load(open(os.path.join(SA, "weapons_table.json"), encoding="utf-8"))
LEVEL = "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eal = unreal.EditorAssetLibrary
snake = lambda s: "".join(c if c.isalnum() else "_" for c in s.lower()).strip("_")
KIND = {k: getattr(unreal.RDSpellKind, k.upper()) for k in ("Bolt", "Lash", "Ward", "Skin", "Dispel", "Drain", "Cloud", "Veil", "Curse", "Raise", "Rune", "Nova",
                                                              "Mirror", "Rend", "Corpse", "Pillar", "Rift", "Pact", "Knight", "Meteors", "Sanctum", "Apocalypse")}
TYPE = {"Offense": unreal.RDSpellType.OFFENSE, "Protection": unreal.RDSpellType.PROTECTION, "Curse": unreal.RDSpellType.CURSE, "Summon": unreal.RDSpellType.SUMMON}
RING = {"Magic": unreal.RDRingKind.MAGIC, "Health": unreal.RDRingKind.HEALTH, "Dexterity": unreal.RDRingKind.DEXTERITY}


def tier_of(mana):
    return 1 if mana <= 15 else 2 if mana <= 30 else 3 if mana <= 60 else 4 if mana <= 110 else 5


if not ues.get_editor_world().get_path_name().startswith(LEVEL + "."): unreal.EditorLoadingAndSavingUtils.load_map(LEVEL)
gen = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
sounds = gen.get_editor_property("sounds")
missing = []


def fx(ref):
    if not ref: return None
    root, rel = ref.split(":", 1)
    p = SP["fx_root"][root] + rel
    if not eal.does_asset_exist(p): missing.append(p); return None
    return unreal.load_asset(p)


# ---- the spells
spells = []; by_tier = {}
for s in SP["spells"]:
    d = unreal.RDSpellDef()
    d.name = s["name"]; d.number = s["n"]; d.type = TYPE[s["type"]]; d.kind = KIND[s["kind"]]; d.effect = s["effect"]
    d.mana = float(s["mana"]); d.cooldown = float(s["cooldown"]); d.duration = float(s["duration"]); d.drop_chance = float(s["drop"]) / 100.0
    d.tier = tier_of(s["mana"])
    dmg = float(s.get("damage", 0))
    # (what lasts: the table's whole over its duration, a second's share)
    if s.get("per_second") and s["duration"] > 0: dmg = round(dmg / s["duration"], 1)
    d.damage = dmg
    for k, prop in (("reach", "reach"), ("radius", "radius"), ("splash", "splash"), ("amount", "amount"), ("slow", "slow"), ("burn", "burn"), ("drain", "drain"), ("speed", "bolt_speed"), ("every", "area_every")):
        if k in s: d.set_editor_property(prop, float(s[k]))
    if "count" in s: d.count = int(s["count"])
    d.pierce = bool(s.get("pierce", False))
    f = s.get("fx", {}); sc = s.get("scale", {})
    for k, prop in (("cast", "cast_fx"), ("bolt", "bolt_fx"), ("impact", "impact_fx"), ("area", "area_fx"), ("shield", "shield_fx")):
        d.set_editor_property(prop, fx(f.get(k)))
        d.set_editor_property(prop + "_scale", float(sc.get(k, 1.0)))
    if "colors" in s:
        d.use_colors = True; d.colors = [unreal.LinearColor(c[0], c[1], c[2], 1.0) for c in s["colors"]]
    if "light" in s:
        l = s["light"]; d.light_color = unreal.LinearColor(l[0], l[1], l[2], 1.0); d.light_intensity = float(l[3])
    snd = s.get("sound", "Fire")
    d.sound_key = snd if f"Player.Cast.{snd}" in sounds else "Fire"
    d.icon = "spell_" + snake(s["name"])
    spells.append(d); by_tier.setdefault(d.tier, []).append(s["name"])
gen.set_editor_property("spells", spells)
SI = {str(d.name): i for i, d in enumerate(spells)}

# ---- the items: rings, tomes; the weapons' types
items = [i for i in gen.get_editor_property("items") if i.kind not in (unreal.RDItemKind.RING, unreal.RDItemKind.TOME)]
wtype = {w["name"]: w["type"] for w in WT["weapons"]}
for i in items:
    if i.kind == unreal.RDItemKind.WEAPON:
        t = wtype.get(str(i.name), "")
        if t == "ranged": t = "crossbow" if "crossbow" in str(i.name).lower() else "bow"
        i.weapon_type = t
R = LT["rings"]; rings = []
for k in R["kinds"]:
    for n in range(1, 11):
        it = unreal.RDItemDef(); it.name = f"{k['name']} {n}"; it.kind = unreal.RDItemKind.RING; it.ring_kind = RING[k["kind"]]
        it.amount = n / 10.0; it.tiers = [(n + 1) // 2]; it.weight = float(R["rarity"]); it.found_max = 1; it.icon = "ring_" + k["kind"].lower()
        items.append(it); rings.append(str(it.name))
T = LT["tomes"]
it = unreal.RDItemDef(); it.name = T["name"]; it.kind = unreal.RDItemKind.TOME; it.weight = float(T["rarity"]); it.tiers = []; it.found_max = 1; it.icon = "tome"
items.append(it)
for d in spells:
    it = unreal.RDItemDef(); it.name = f"Tome of {d.name}"; it.kind = unreal.RDItemKind.TOME; it.spell = d.name; it.weight = 0.0
    it.tiers = [d.tier]; it.found_max = 1; it.icon = str(d.icon)
    items.append(it)
gen.set_editor_property("items", items)

# ---- breaking weapons down, the containers' chance, corpses, the menu, the knight
bds = []
for b in LT["breakdown"]["types"]:
    bd = unreal.RDBreakdown(); bd.types = list(b["types"]); bd.gives = list(b["gives"].keys()); bd.per_tier = [int(v) for v in b["gives"].values()]
    bds.append(bd)
gen.set_editor_property("breakdowns", bds)
gen.set_editor_property("container_loot_chance", float(LT["container_chance"]["chance"]))
gen.set_editor_property("keep_corpses", True)
gen.set_editor_property("escape_menu", True)
gen.set_editor_property("knight_monster", SP["knight"]["monster"])
gen.set_editor_property("knight_strength", float(SP["knight"]["strength"]))

# ---- the heroes: what they learn and wear; their own spells become the table's
who = {}
for k in R["kinds"]:
    for h in k["who"]: who.setdefault(h, []).append(RING[k["kind"]])
heroes = list(gen.get_editor_property("heroes")); learned = {}
for h in heroes:
    n = str(h.name)
    h.learns = [TYPE[t] for t in SP["learns"].get(n, [])]
    h.ring_kinds = who.get(n, [])
    ws = list(h.weapons)
    for w in ws:
        sname = SP["starting"].get(str(w.name))
        if not sname: continue
        d = spells[SI[sname]]
        # (spell_index: the table's; spell: its bSpell, which a first run of this set to the index's truth by a name clash)
        w.spell_index = SI[sname]; w.spell = True; w.cooldown = d.cooldown
        w.charge_effect = d.cast_fx; w.charge_effect_scale = d.cast_fx_scale
        w.bolt_effect = d.bolt_fx; w.bolt_effect_scale = d.bolt_fx_scale; w.bolt_core_effect = None
        w.burst_effect = d.impact_fx; w.burst_effect_scale = d.impact_fx_scale; w.burst_flame_effect = None
        w.spell_light_color = d.light_color; w.spell_light_intensity = d.light_intensity
    h.weapons = ws
    learned[n] = [str(t.name) for t in h.learns] + ["rings " + ", ".join(str(r.name) for r in h.ring_kinds)] + [f"{w.name}->{spells[w.spell_index].name} (a spell: {w.spell})" for w in ws if w.spell_index >= 0]
gen.set_editor_property("heroes", heroes)
gen.modify()
les.save_current_level()
# ---- the editor's stop key
stop = unreal.RDDungeonGenerator.move_editor_stop_key(True)
back = gen.get_editor_property("spells")
print("RDM5SPELLS", json.dumps({"spells": len(back), "by tier": by_tier, "tier drop sums": {t: round(sum(float(d.drop_chance) for d in back if d.tier == t), 4) for t in by_tier},
                                "missing fx": missing, "rings": len(rings), "tomes": 1 + len(spells), "heroes": learned, "breakdowns": len(bds),
                                "container chance": gen.get_editor_property("container_loot_chance"), "keep corpses": gen.get_editor_property("keep_corpses"),
                                "escape menu": gen.get_editor_property("escape_menu"), "stop key": stop}, ensure_ascii=False))
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
