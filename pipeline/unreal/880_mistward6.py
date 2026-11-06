"""mistward_castle, the list of 2026-11-01 (docs/improvements6.txt): the Rogue's stealth and the heroes balanced against each
other tier by tier (SourceArt/mistward/balance6.json; C++ RD/RDMistward6.cpp). On mistward_castle and brokenspire:
- the generator's switches bStealth and bTierGrowth on
- each hero's numbers: hit points; for each tier open past the first, the share more hit points, spell / chi damage and damage
  of her own weapons (her fists, her starting blades and crossbow; a found weapon carries its own tier instead); mana back a
  second as a share of her pool; the Summoner (2026-11-05): her pool (60, the Warlock's), more mana per tier, her summons
  growing with the tiers (the generator's SummonTierStrength), how many of a summoning she leads (summon_counts: 3 Spiders)
- the Rogue: her dexterity energy, a stealth's cost and length, the ambush (balance6.json's numbers: 100, 1.5 a second back,
  40 a stealth, 8 s, +75 %), her daggers and crossbow (13 and 26: the ambush and her rings are her growth), her card's line
  and the controls panel's
- found weapons: 8 + 3 x the damage rating, times weapon_tier_power by the first tier the weapon is found in
- the Martial Artist's chi attacks: base x (mana / base_mana) ^ power (23 for the Straight Punch's 7 mana, 154 for the
  Spinning Kick's 88), in the spell table and on her weapons and locked weapons
Brokenspire (the town and its wilds) gets the same: a Save As copy of the castle, it keeps a copy of the heroes, and her pool
and summons are the level's own there (the PR review's find: carried from the castle at 84 mana she was clamped to the town's
50). Then the hero menu (mistward_castle_select) gets the heroes as the castle has them (its cards), and the castle is opened
again. A key left out of balance6.json puts back what 876 set (the Summoner's mana, her summonings' counts: summoner4.json).
Writes SourceArt/mistward/balance_state.json: the game's numbers as set (mw_balance.py models from it; the docs' tables).
Run after 879 (and again after anything that writes the castle's heroes: 825, 862, 870, 871, 872, 876). Args: none"""
import json, os, unreal
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt"
B = json.load(open(os.path.join(SA, "mistward", "balance6.json"), encoding="utf-8"))
MA = json.load(open(os.path.join(SA, "martial_arts", "martial_arts.json"), encoding="utf-8"))
S4 = json.load(open(os.path.join(SA, "mistward", "summoner4.json"), encoding="utf-8"))
MAP = "/Game/RandomDungeon/Maps/mistward_castle"; MENU = "/Game/RandomDungeon/Maps/mistward_castle_select"
TOWN = "/Game/RandomDungeon/Maps/brokenspire"
WP = B["weapon_tier_power"]
# (876's numbers, put back when balance6.json leaves them out: her pool, how many of each summoning she leads)
BASE_MANA = {"Summoner": float(S4["mana"])}
BASE_COUNTS = {f"Summon Tier {k + 1}": int(n) for k, (_, n) in enumerate(S4["summons"])}


def gen_of(w):
    gs = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDDungeonGenerator); assert gs, "no generator"; return gs[0]


def balance(g):
    """the balance on one level's generator: its switches, found weapons, chi, the summonings, the heroes"""
    g.set_editor_property("summon_tier_strength", [float(x) for x in B["summon_tier_strength"]])

    # ---- found weapons: their damage by their tier
    items = list(g.get_editor_property("items")); nw = 0
    for it in items:
        if it.kind != unreal.RDItemKind.WEAPON: continue
        t = max(1, min(min(it.tiers) if len(it.tiers) else 1, len(WP)))
        fits = list(it.get_editor_property("weapon_fits"))
        for f in fits:
            wd = f.get_editor_property("weapon")
            base = 8 + 3 * wd.get_editor_property("damage_rating")
            wd.set_editor_property("damage", float(round(base * WP[t - 1])))
            f.set_editor_property("weapon", wd); nw += 1
        it.set_editor_property("weapon_fits", fits)
    g.set_editor_property("items", items)

    # ---- the chi attacks: damage by mana
    C = B["chi"]; CHI = {m["name"] for m in MA["chi"]}
    spells = list(g.get_editor_property("spells")); chi = {}
    for s in spells:
        nm = str(s.get_editor_property("name"))
        if nm in CHI:
            d = float(round(C["base"] * (s.get_editor_property("mana") / C["base_mana"]) ** C["power"]))
            s.set_editor_property("damage", d); chi[nm] = d
    # ---- the Summoner's summonings: how many of each she leads (balance6.json's summon_counts; the rest as 876 set them)
    SC = dict(BASE_COUNTS); SC.update(B["heroes"]["Summoner"].get("summon_counts", {})); counts = {}
    for s in spells:
        nm = str(s.get_editor_property("name"))
        if nm in SC: s.set_editor_property("count", int(SC[nm])); counts[nm] = int(SC[nm])
    assert sorted(counts) == sorted(SC), ("summonings not found", SC, counts)
    g.set_editor_property("spells", spells)
    assert len(chi) == 10, ("chi spells found", sorted(chi))

    # ---- the heroes
    heroes = list(g.get_editor_property("heroes")); done = {}
    for h in heroes:
        n = str(h.name); hb = B["heroes"].get(n)
        if not hb: continue
        h.set_editor_property("max_health", float(hb["hp"]))
        h.set_editor_property("health_per_tier", hb["health_per_tier"]); h.set_editor_property("spell_power_per_tier", hb["spell_power_per_tier"])
        h.set_editor_property("own_weapon_power_per_tier", hb["own_weapon_power_per_tier"]); h.set_editor_property("mana_regen_share", hb["mana_regen_share"])
        # (the Summoner's balance of 2026-11-05: her pool (876's when left out), its growth per tier, her summons growing)
        mana = hb.get("mana", BASE_MANA.get(n))
        if mana is not None: h.set_editor_property("max_mana", float(mana))
        h.set_editor_property("mana_per_tier", float(hb.get("mana_per_tier", 0.0))); h.set_editor_property("summons_grow", bool(hb.get("summons_grow", False)))
        st = hb.get("stealth", {})
        h.set_editor_property("dex_energy", float(st.get("energy", 0))); h.set_editor_property("dex_per_second", float(st.get("per_second", 0)))
        h.set_editor_property("stealth_cost", float(st.get("cost", 0))); h.set_editor_property("stealth_seconds", float(st.get("seconds", 0)))
        h.set_editor_property("ambush_bonus", float(st.get("ambush", 0)))
        def fix(lst):
            out = []
            for wd in lst:
                wn = str(wd.get_editor_property("name"))
                if wn in hb.get("weapons", {}): wd.set_editor_property("damage", float(hb["weapons"][wn]))
                if wn in chi: wd.set_editor_property("damage", chi[wn])
                out.append(wd)
            return out
        h.set_editor_property("weapons", fix(list(h.weapons))); h.set_editor_property("locked_weapons", fix(list(h.locked_weapons)))
        # (the card's line and the controls panel's for her stealth: once)
        if hb.get("card"):
            ab = [a for a in h.abilities if not a.startswith("Stealth")]
            h.set_editor_property("abilities", ab + [hb["card"]])
            h.set_editor_property("controls_keys", [k for k in h.controls_keys if not k.startswith("Q|")] + hb["keys"])
            h.set_editor_property("controls_pad", [k for k in h.controls_pad if not k.startswith("LB|stealth")] + hb["pad"])
        done[n] = {"hp": h.max_health, "mana": h.max_mana, "abilities": list(h.abilities), "weapons": {str(x.name): x.damage for x in h.weapons}}
    g.set_editor_property("heroes", heroes)
    assert len(done) == 6, sorted(done)
    return nw, chi, counts, done, heroes, items, spells


w = ues.get_editor_world()
if w.get_name() != "mistward_castle": les.load_level(MAP); w = ues.get_editor_world()
g = gen_of(w)
nw, chi, counts, done, heroes, items, spells = balance(g)
C = B["chi"]

# ---- the state the model reads (the game's numbers as set)
def wdef(x):
    atk = list(x.get_editor_property("attacks")); st_ = list(x.get_editor_property("attack_starts")); en = list(x.get_editor_property("attack_ends"))
    lens = []
    for k, cl in enumerate(atk):
        t0 = st_[k] if k < len(st_) else 0.0
        t1 = en[k] if k < len(en) and en[k] > t0 else (cl.get_play_length() if cl else 0.0)
        lens.append(round(t1 - t0, 3))
    return {"name": str(x.name), "damage": x.damage, "reach": x.reach, "rate": round(x.play_rate, 4), "clip_s": lens, "spell": x.get_editor_property("spell"),
            "mana": x.mana_cost, "cooldown": x.cooldown, "spell_index": x.spell_index, "type": str(x.weapon_type), "crossbow": x.bolt_mesh is not None,
            "mana_share": x.mana_share, "alongside": x.get_editor_property("alongside"), "rating": x.damage_rating}
S_ = {"heroes": [], "weapons": [], "armour": [], "shields": [], "rings": [], "spells": [], "monsters": []}
for h in heroes:
    S_["heroes"].append({"name": str(h.name), "title": h.title, "hp": h.max_health, "mana": h.max_mana, "regen": h.mana_per_second, "melee": round(h.melee_bonus, 3),
                         "ranged": round(h.ranged_bonus, 3), "type_bonus": {str(k): round(v, 3) for k, v in h.type_bonus.items()}, "dex_types": [str(x) for x in h.dexterity_types],
                         "wears": [str(x).split(".")[-1].split(":")[0] for x in h.wears], "rings": [str(x).split(".")[-1].split(":")[0] for x in h.ring_kinds],
                         "health_per_tier": h.health_per_tier, "spell_power_per_tier": h.spell_power_per_tier, "own_weapon_power_per_tier": h.own_weapon_power_per_tier,
                         "mana_regen_share": h.mana_regen_share, "mana_per_tier": round(h.mana_per_tier, 3), "summons_grow": h.summons_grow, "dex_energy": h.dex_energy, "dex_per_second": h.dex_per_second, "stealth_cost": h.stealth_cost,
                         "stealth_seconds": h.stealth_seconds, "ambush": h.ambush_bonus, "per_boss": h.unlock_per_boss,
                         "weapons": [wdef(x) for x in h.weapons], "locked": [wdef(x) for x in h.locked_weapons]})
for it in items:
    k = str(it.kind).split(".")[-1].split(":")[0]
    if k == "WEAPON": S_["weapons"].append({"name": str(it.name), "tiers": list(it.tiers), "fits": {str(f.hero): wdef(f.weapon) for f in it.weapon_fits}})
    elif k == "ARMOUR": S_["armour"].append({"name": str(it.name), "tiers": list(it.tiers), "amount": round(it.amount, 3), "slower": round(it.slower, 3), "weight": str(it.armour_weight).split(".")[-1].split(":")[0]})
    elif k == "SHIELD": S_["shields"].append({"name": str(it.name), "tiers": list(it.tiers), "amount": round(it.amount, 3), "slower": round(it.slower, 3)})
    elif k == "RING": S_["rings"].append({"name": str(it.name), "tiers": list(it.tiers), "amount": round(it.amount, 3), "kind": str(it.ring_kind).split(".")[-1].split(":")[0]})
for s in spells:
    S_["spells"].append({"name": str(s.name), "kind": str(s.kind).split(".")[-1].split(":")[0], "damage": s.damage, "mana": s.mana, "cooldown": s.cooldown,
                         "duration": s.duration, "radius": s.radius, "count": s.count, "amount": round(s.amount, 3), "tier": s.tier})
for m in g.get_editor_property("monsters"):
    S_["monsters"].append({"name": str(m.name), "title": str(m.title), "tier": m.tier, "hf": round(m.health_factor, 3), "df": round(m.damage_factor, 3),
                           "interval": round(m.attack_interval, 3), "shoots": m.shoots})
for k in ("tier_health", "tier_damage", "tier_speed", "tier_attack_interval", "tier_ability"): S_[k] = [round(x, 3) for x in g.get_editor_property(k)]
for k in ("boss_health", "boss_damage", "monster_reference_health", "monster_reference_blow", "block_share", "chase_speed_scale"): S_[k] = round(g.get_editor_property(k), 3)
S_["weapon_tier_power"] = WP; S_["chi"] = C; S_["summon_tier_strength"] = [round(x, 3) for x in g.get_editor_property("summon_tier_strength")]
json.dump(S_, open(os.path.join(SA, "mistward", "balance_state.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
HTXT = [h.export_text() for h in heroes]
les.save_current_level()
print("RD880 castle:", nw, "weapon fits,", len(chi), "chi", chi, "| summonings", counts, "| heroes", json.dumps(done)[:1500])
del g, heroes, items, spells

# ---- Brokenspire (the town and its wilds): the same, on its own copy of the heroes
les.load_level(TOWN); g = gen_of(ues.get_editor_world())
tw = balance(g)
les.save_current_level()
print("RD880 brokenspire:", tw[0], "weapon fits,", len(tw[1]), "chi | summonings", tw[2], "| mana", {k: v["mana"] for k, v in tw[3].items()})
del g, tw

# ---- the menu's cards: the heroes as the castle has them
les.load_level(MENU); w = ues.get_editor_world()
sel = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.RDHeroSelect)
assert sel, "no hero menu"
old = [str(h.name) for h in sel[0].get_editor_property("heroes")]
new = []
for t in HTXT:
    h = unreal.RDHeroDef(); h.import_text(t)
    if str(h.name) in old: new.append(h)
new.sort(key=lambda h: old.index(str(h.name)))
assert [str(h.name) for h in new] == old, (old, [str(h.name) for h in new])
sel[0].set_editor_property("heroes", new)
les.save_current_level()
print("RD880 menu:", old, "| rogue card:", [list(h.abilities) for h in new if str(h.name) == "Rogue"])
les.load_level(MAP)
del sel, new
import gc; gc.collect()
