"""The rebalance to tier 25 (the user's list of 2026-11-08b, docs/improvements9.txt, its fifth phase: "mage spells need to be
limited to 1 gained per tier, then the rest need to be redistributed in the rest of the 5 ... if there are not enough mage
spells, there needs to be more made up, assigned damage and balanced all the way to Heaven; additional summoner, rogue, and
martial artist abilities need to be created after the mistward castle dungeon is defeated so that they can be earned in the
other dungeons; the armor and weapons need to be redistributed across the rest of the 5 dungeons and then rebalanced - or more
armor and weapons need to be made up ...; rebalance and redistribute all monsters so that they're spread out from brokenspire
to Heaven"), from SourceArt/balance/tier25.json, onto every map of the game (brokenspire and the six dungeons):
- the level's tiers in the game's (DungeonTierBase, DungeonTierCap: Mistward Castle 1-5, Vel Morrath 6-10, The War Engine 11-15,
  the Sewers 16-20, Kethrys Spire 21-25, Heaven 25)
- the monsters' tier tables to 25 (hit points x1.12 a tier past 5, blows x1.09; speed, pace and ability as tier 5's), the
  summonings' strengths to 10
- the Mage's spells: each tome spell one place among the dungeons' 30 tiers (Slot), in their old order; two made up (Starfall,
  Singularity) with their tomes
- the gear: each tiered weapon, armour, shield and ring again in each later dungeon at its tier there in a quality (Fine,
  Masterwork, Exalted, Celestial: damage by the tiers' power, armour, block and bonus a little more, durability more); potions and
  food in each dungeon at their rank
- the monsters: every dungeon's kinds on every map (weight 0 but on their own map: summonable, met in the wilds), each with its
  band of the wilderness's tiers (the castle's 1-10, the War Engine's 11-15, the drowned 16-20, the casters 21-25, the defenders
  23-25); Aurorim never in the wilds
- the later abilities: the Summoner's summonings of the later dungeons' kinds, the Martial Artist's stronger chi attacks, the
  Rogue's bolts and blades, one of each in each later dungeon (FRDHeroDef::LaterWeapons: its last tier's boss)
Run after 880 (its found weapons' rule, balance6.json's weapon_tier_power, is carried past tier 5 here) and after every stage that
writes the levels' heroes, spells, items or monsters anew; then 905 (the chain's tier bases). C++ first.
Args: [map ...] (default: all seven)"""
import os, sys, json, math, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "claude_ue5", "SourceArt"))
D = json.load(open(os.path.join(SA, "balance", "tier25.json"), encoding="utf-8"))
MAPS = [a for a in sys.argv[1:] if a in D["maps"]] or list(D["maps"].keys())
Q = D["qualities"]
QSET = tuple(q + " " for q in Q)


def open_map(m):
    path = "/Game/RandomDungeon/Maps/" + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def copy_struct(cls, s):
    x = cls(); x.import_text(s.export_text()); return x


BAL6 = json.load(open(os.path.join(SA, "mistward", "balance6.json"), encoding="utf-8"))


def tier_power(t):
    """a found weapon's damage factor by its first tier (880's balance6.json for 1-5), past 5 the hero's power growth a tier"""
    wtp = BAL6["weapon_tier_power"]
    return wtp[t - 1] if t <= 5 else wtp[4] * D["power_growth"] ** (t - 5)


# ---------------------------------------------------------------- first: every dungeon's own kinds, read on its own map
HOME = D["monsters"]["home"]; own = {}
for m, j in HOME.items():
    names = {e["name"] for e in json.load(open(os.path.join(SA, j, "monsters.json"), encoding="utf-8"))["monsters"]}
    g = open_map(m)
    for d in g.get_editor_property("monsters"):
        if str(d.get_editor_property("name")) in names: own[str(d.get_editor_property("name"))] = (m, d.export_text())
    del g
print("T25 own kinds:", {m: sum(1 for v in own.values() if v[0] == m) for m in HOME})

report = {}
for m in MAPS:
    base, cap = D["maps"][m]
    g = open_map(m)
    r = report.setdefault(m, {})
    g.set_editor_property("dungeon_tier_base", base); g.set_editor_property("dungeon_tier_cap", cap)
    # ------------------------------------------------------------ the tier tables to 25
    th = list(g.get_editor_property("tier_health"))[:5]; td = list(g.get_editor_property("tier_damage"))[:5]
    ts = list(g.get_editor_property("tier_speed"))[:5]; ti = list(g.get_editor_property("tier_attack_interval"))[:5]; ta = list(g.get_editor_property("tier_ability"))[:5]
    n = D["tiers"]["count"]
    g.set_editor_property("tier_health", th + [th[4] * D["tiers"]["health_growth"] ** k for k in range(1, n - 4)])
    g.set_editor_property("tier_damage", td + [td[4] * D["tiers"]["damage_growth"] ** k for k in range(1, n - 4)])
    for prop, v in (("tier_speed", ts), ("tier_attack_interval", ti), ("tier_ability", ta)): g.set_editor_property(prop, v + [v[4]] * (n - 5))
    g.set_editor_property("summon_tier_strength", D["summon_tier_strength"])
    # (the hero's growth past tier 5: her power as the monsters' hit points, her hit points and mana as their blows)
    g.set_editor_property("tier_growth_power", D["power_growth"]); g.set_editor_property("tier_growth_health", D["health_growth"])
    r["tiers"] = [round(x, 2) for x in g.get_editor_property("tier_health")][::4]
    # ------------------------------------------------------------ the spells: one to each of the dungeons' tiers; the made-up ones
    later = D["later"]
    made = {s["name"] for s in D["new_spells"]} | {e["name"] for e in later["Summoner"]} | {e["name"] for e in later["MartialArtist"]}
    spells = [s for s in g.get_editor_property("spells") if str(s.get_editor_property("name")) not in made]
    by = {str(s.get_editor_property("name")): s for s in spells}
    # (numbers of their own (PR #34's review: max + 1 met the later summonings' 206-210): the made-up spells 301 on, the later chi
    # attacks 311 on; the stages take out spells by number (872 101-199, 876 201-205, 875 keeps 1-100))
    for k_, e in enumerate(D["new_spells"]):
        s = copy_struct(unreal.RDSpellDef, by[e["from"]])
        s.set_editor_property("name", e["name"]); s.set_editor_property("number", 301 + k_)
        s.set_editor_property("mana", s.get_editor_property("mana") * e["mana"]); s.set_editor_property("damage", s.get_editor_property("damage") * e["damage"])
        s.set_editor_property("effect", e["effect"]); spells.append(s)
    excl = set(D["starting_spells"]) | set(D["tome_spells_exclude"])
    tome = [s for s in spells if str(s.get_editor_property("name")) not in excl and str(s.get_editor_property("name")) not in {e["name"] for e in D["new_spells"]}]
    tome.sort(key=lambda s: (int(s.get_editor_property("tier")), float(s.get_editor_property("mana")), int(s.get_editor_property("number"))))
    tome += [s for s in spells if str(s.get_editor_property("name")) in {e["name"] for e in D["new_spells"]}]
    for s in spells: s.set_editor_property("slot", 0)
    for k, s in enumerate(tome): s.set_editor_property("slot", k + 1)
    r["slots"] = [str(s.get_editor_property("name")) for s in tome]
    # (the later abilities' spells: summonings of the later dungeons' kinds, stronger chi attacks)
    for e in later["Summoner"]:
        s = copy_struct(unreal.RDSpellDef, by[e["from_spell"]])
        for k, v in (("name", e["name"]), ("number", 200 + e["tier"]), ("tier", e["tier"]), ("summon_kind", e["kind"]), ("count", e["count"]), ("effect", e["effect"]),
                     ("icon", e["icon"]), ("slot", 0)): s.set_editor_property(k, v)
        s.set_editor_property("mana", s.get_editor_property("mana") * (1.0 + 0.12 * (e["tier"] - 5)))
        spells.append(s)
    for k_, e in enumerate(later["MartialArtist"]):
        s = copy_struct(unreal.RDSpellDef, by[e["from_spell"]])
        s.set_editor_property("name", e["name"]); s.set_editor_property("number", 311 + k_); s.set_editor_property("slot", 0)
        s.set_editor_property("damage", s.get_editor_property("damage") * e["damage"]); s.set_editor_property("tier", 5)
        spells.append(s)
    g.set_editor_property("spells", spells)
    idx = {str(s.get_editor_property("name")): i for i, s in enumerate(spells)}
    # ------------------------------------------------------------ the items: the qualities, the consumables in every dungeon, the
    # new tomes
    items = [it for it in g.get_editor_property("items") if not str(it.get_editor_property("name")).startswith(QSET)
             and str(it.get_editor_property("name")) not in {"Tome of " + e["name"] for e in D["new_spells"]}]
    kinds = {k: getattr(unreal.RDItemKind, k.upper()) for k in D["quality_kinds"] + D["consumable_kinds"]}
    added = {q: 0 for q in Q}; out = []
    for it in items:
        kd = it.get_editor_property("kind"); tiers = list(it.get_editor_property("tiers"))
        if kd in [kinds[k] for k in D["consumable_kinds"]] and tiers:
            it.set_editor_property("tiers", sorted({t + 5 * q for t in tiers for q in range(5) if t + 5 * q <= 25}))
        out.append(it)
        if kd not in [kinds[k] for k in D["quality_kinds"]] or not tiers or max(tiers) > 5: continue
        name = str(it.get_editor_property("name"))
        for q, qn in enumerate(Q, start=1):
            nt = [t + 5 * q for t in tiers if t + 5 * q <= 25]
            if not nt: continue
            c = copy_struct(unreal.RDItemDef, it); nn = f"{qn} {name}"
            c.set_editor_property("name", nn); c.set_editor_property("tiers", nt)
            c.set_editor_property("durability", it.get_editor_property("durability") * (1.0 + D["quality_durability_step"] * q))
            if kd == kinds["Weapon"]:
                c.set_editor_property("amount", it.get_editor_property("amount") * (1.0 + D["quality_durability_step"] * q))   # (a weapon's durability)
                fits = []
                for wf in c.get_editor_property("weapon_fits"):
                    # (880's rule, 8 + 3 x the damage rating times the power of its first tier, at the copy's tier)
                    w = wf.get_editor_property("weapon"); w.set_editor_property("name", nn)
                    w.set_editor_property("damage", float(round((8 + 3 * w.get_editor_property("damage_rating")) * tier_power(min(nt)))))
                    wf.set_editor_property("weapon", w); fits.append(wf)
                c.set_editor_property("weapon_fits", fits)
                c.set_editor_property("looks", f"{qn.lower()} make  ·  " + str(it.get_editor_property("looks")))
            elif kd in (kinds["Armour"], kinds["Shield"]):
                c.set_editor_property("amount", min(it.get_editor_property("amount") + D["quality_armour_step"] * q, D["quality_armour_max"]))
                if kd == kinds["Shield"]:
                    fits = []
                    for wf in c.get_editor_property("weapon_fits"):
                        w = wf.get_editor_property("weapon"); w.set_editor_property("name", nn); wf.set_editor_property("weapon", w); fits.append(wf)
                    c.set_editor_property("weapon_fits", fits)
            elif kd == kinds["Ring"]:
                c.set_editor_property("amount", it.get_editor_property("amount") * (1.0 + D["quality_ring_step"] * q))
            out.append(c); added[qn] += 1
    tomes = {str(it.get_editor_property("name")): it for it in out if it.get_editor_property("kind") == unreal.RDItemKind.TOME}
    for e in D["new_spells"]:
        src = tomes.get("Tome of " + e["from"])
        if not src: continue
        c = copy_struct(unreal.RDItemDef, src); c.set_editor_property("name", "Tome of " + e["name"]); c.set_editor_property("spell", e["name"])
        out.append(c)
    # (each spell's tome in the game's tier of its place: slot k is dungeon k // 5's tier k % 5, Heaven's all 25)
    slot = {str(s.get_editor_property("name")): int(s.get_editor_property("slot")) for s in spells}
    for it in out:
        nm = str(it.get_editor_property("name"))
        if it.get_editor_property("kind") == unreal.RDItemKind.TOME and nm.startswith("Tome of ") and slot.get(nm[8:], 0) > 0:
            it.set_editor_property("tiers", [min(slot[nm[8:]], 25)])
    g.set_editor_property("items", out)
    r["items"] = {"all": len(out), **added}
    # ------------------------------------------------------------ the monsters: every dungeon's on every map, their wild bands
    mons = list(g.get_editor_property("monsters"))
    have = {str(d.get_editor_property("name")) for d in mons}
    for nm, (home, txt) in own.items():
        if nm in have: continue
        d = unreal.RDMonsterDef(); d.import_text(txt); d.set_editor_property("weight", 0.0); mons.append(d)
    bands = D["monsters"]["wild_bands"]
    for d in mons:
        nm = str(d.get_editor_property("name")); t = int(d.get_editor_property("tier"))
        if nm in D["monsters"]["never_wild"] or t < 1:
            d.set_editor_property("wild_tier_min", 99); d.set_editor_property("wild_tier_max", 99); continue
        home = own[nm][0] if nm in own else "castle"
        b = bands[home]
        lo, hi = (b[min(t, 5) - 1] if home == "castle" else (b if isinstance(b, list) else [b + t, b + t]))
        d.set_editor_property("wild_tier_min", lo); d.set_editor_property("wild_tier_max", hi)
    g.set_editor_property("monsters", mons)
    r["monsters"] = len(mons)
    # ------------------------------------------------------------ the later abilities
    heroes = list(g.get_editor_property("heroes"))
    for h in heroes:
        hn = str(h.get_editor_property("name"))
        if hn not in later: h.set_editor_property("later_weapons", []); continue
        pool = {str(w.get_editor_property("name")): w for w in list(h.get_editor_property("weapons")) + list(h.get_editor_property("locked_weapons"))}
        lw = []
        for e in later[hn]:
            src = pool.get(e.get("from_spell") or e.get("from_weapon"))
            if src is None and hn == "Summoner": src = pool.get("Summon Tier 5")
            if src is None: print("T25 no", e.get("from_spell") or e.get("from_weapon"), "for", hn); continue
            w = copy_struct(unreal.RDWeaponDef, src); w.set_editor_property("name", e["name"])
            if e["name"] in idx: w.set_editor_property("spell_index", idx[e["name"]])
            if "damage" in e: w.set_editor_property("damage", w.get_editor_property("damage") * e["damage"])
            if "reach" in e: w.set_editor_property("reach", float(e["reach"]))
            if "splash" in e: w.set_editor_property("bolt_splash", float(e["splash"]))
            if "burst" in e: w.set_editor_property("burst_effect", unreal.load_asset(e["burst"]))
            if "bolt" in e: w.set_editor_property("bolt_effect", unreal.load_asset(e["bolt"]))
            lw.append(w)
        h.set_editor_property("later_weapons", lw)
        r.setdefault("later", {})[hn] = [str(w.get_editor_property("name")) for w in lw]
    g.set_editor_property("heroes", heroes)
    # (every spell weapon at its spell's place again (the table grew): the heroes' own and locked)
    heroes = list(g.get_editor_property("heroes"))
    for h in heroes:
        for prop in ("weapons", "locked_weapons", "later_weapons"):
            ws = list(h.get_editor_property(prop))
            for w in ws:
                nm = str(w.get_editor_property("name"))
                if w.get_editor_property("spell") and nm in idx: w.set_editor_property("spell_index", idx[nm])
            h.set_editor_property(prop, ws)
    g.set_editor_property("heroes", heroes)
    g.modify()
    les.save_current_level()
    print("T25", m, json.dumps(r))
    del g, mons, heroes, spells, items, out
import gc
gc.collect()
