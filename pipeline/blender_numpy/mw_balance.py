"""mistward_castle's balance tables (the list of 2026-11-01, docs/improvements6.txt), written from the game's own numbers:
SourceArt/mistward/balance_state.json (880 writes it from the castle's generator after setting balance6.json) and the balance
trials' record (868's balance step: SourceArt/mistward/test_<tag>.json). Each table goes between its markers in
docs/levels/mistward_castle.md (<!-- mw6:heroes -->, <!-- mw6:own -->, <!-- mw6:found -->, <!-- mw6:chi -->, <!-- mw6:kits -->,
<!-- mw6:trials -->, each closed by <!-- /mw6:... -->).
- a hero's damage a hit: her weapon's damage x (1 + her melee / ranged / type bonus) x her growth (her own weapons and her
  spells by the tiers open past the first); a second: over her attack clips at their play rate (spells: over their cast)
Args: [trial tag] (default b: test_b.json; none found: the trials' table is left as it is). python 3, no other packages"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, "..", ".."); SA = os.path.join(ROOT, "claude_ue5", "SourceArt", "mistward")
ST = json.load(open(os.path.join(SA, "balance_state.json"), encoding="utf-8"))
B = json.load(open(os.path.join(SA, "balance6.json"), encoding="utf-8"))
TAG = sys.argv[1] if len(sys.argv) > 1 else "b"
TITLE = {h["name"]: (h["title"] or h["name"]).title() for h in ST["heroes"]}
WP = ST["weapon_tier_power"]


def cycle(w):
    """seconds an attack takes: its clips' mean length over its play rate"""
    c = [x for x in w["clip_s"] if x > 0]
    return (sum(c) / len(c)) / max(w["rate"], 0.1) if c else 1.0


def bonus(h, w):
    """her bonus on a weapon of hers (no ring): melee, ranged (a crossbow), her type bonus; none on a spell"""
    if w["spell"] and not w["crossbow"]: return 0.0
    b = h["melee"] if not w["spell"] else h["ranged"]
    return b + h["type_bonus"].get(w["type"], 0.0)


def grow(h, w, t):
    if w["spell"] and not w["crossbow"]: return 1 + h["spell_power_per_tier"] * (t - 1)
    return 1 + h["own_weapon_power_per_tier"] * (t - 1)


def f0(x): return ("%.0f" % x) if abs(x - round(x)) < 0.05 or x >= 20 else ("%.1f" % x)


tables = {}
# ---- the heroes
rows = ["| Hero | Hit points with tiers 1 / 2 / 3 / 4 / 5 open | Mana (back a second) | Each tier opened past the first | Abilities |", "|---|---|---|---|---|"]
for h in ST["heroes"]:
    hp = " / ".join(f0(round(h["hp"] * (1 + h["health_per_tier"] * (t - 1)))) for t in range(1, 6))
    mana = "none" if h["mana"] <= 0 else ("%s (%s: %s %% of her pool)" % (f0(h["mana"]), f0(h["mana"] * h["mana_regen_share"]), f0(h["mana_regen_share"] * 100)) if h["mana_regen_share"] > 0 else "%s (%s)" % (f0(h["mana"]), f0(h["regen"])))
    g = ["+%s %% hit points" % f0(h["health_per_tier"] * 100)]
    if h["spell_power_per_tier"] > 0: g.append("+%s %% %s" % (f0(h["spell_power_per_tier"] * 100), "chi" if h["name"] == "MartialArtist" else "spell damage"))
    if h["own_weapon_power_per_tier"] > 0: g.append("+%s %% damage of her own %s" % (f0(h["own_weapon_power_per_tier"] * 100), "fists" if h["name"] == "MartialArtist" else "weapons"))
    if h["name"] == "Warrior": g[-1] += " (her own dagger stays the worst weapon: she grows by what she finds)"
    ab = []
    if h["dex_energy"] > 0: ab.append("stealth: %s of %s dexterity energy (back %s a second; a speed potion fills it), %s s unseen by monsters and traps, her first blow out of it +%s %%"
                                      % (f0(h["stealth_cost"]), f0(h["dex_energy"]), f0(h["dex_per_second"]), f0(h["stealth_seconds"]), f0(h["ambush"] * 100)))
    if h["melee"] > 0: ab.append("+%s %% melee" % f0(h["melee"] * 100))
    if h["ranged"] > 0: ab.append("+%s %% ranged" % f0(h["ranged"] * 100))
    for k, v in h["type_bonus"].items(): ab.append("+%s %% %s" % (f0(v * 100), k))
    rows.append("| %s | %s | %s | %s | %s |" % (TITLE[h["name"]], hp, mana, ", ".join(g), "; ".join(ab) or "-"))
tables["heroes"] = rows
# ---- her own attacks, tier 1 and tier 5
rows = ["| Hero | Her own weapon or spell (mana) | Damage a hit, tiers 1 / 3 / 5 | A second, tier 1 / tier 5 |", "|---|---|---|---|"]
for h in ST["heroes"]:
    for w in h["weapons"] + h["locked"]:
        if w["damage"] <= 0: continue
        d = [w["damage"] * (1 + bonus(h, w)) * grow(h, w, t) for t in (1, 3, 5)]
        nm = w["name"] + (" (%s)" % f0(w["mana"]) if w["mana"] > 0 else "") + (" (locked: a boss)" if w in h["locked"] else "")
        rows.append("| %s | %s | %s | %s / %s |" % (TITLE[h["name"]], nm, " / ".join(f0(x) for x in d), f0(d[0] / cycle(w)), f0(d[2] / cycle(w))))
tables["own"] = rows
# ---- found weapons
rows = ["| Weapon | Type | Tier | Damage a hit (8 + 3 x its rating, x its tier's power) | Before |", "|---|---|---|---|---|"]
for w in sorted(ST["weapons"], key=lambda w: (min(w["tiers"] or [1]), w["name"])):
    f = next(iter(w["fits"].values())); t = min(w["tiers"] or [1])
    rows.append("| %s | %s | %s | %s (x %s) | %s |" % (w["name"], f["type"] or "ranged", ", ".join(str(x) for x in w["tiers"]), f0(f["damage"]), WP[t - 1], f0(8 + 3 * f["rating"])))
tables["found"] = rows
# ---- chi
C = ST["chi"]; MA = next(h for h in ST["heroes"] if h["name"] == "MartialArtist")
rows = ["| Chi attack | Mana | Damage (tier 1) | With tiers 2-5 open (x 1.12 / 1.24 / 1.36 / 1.48) | Before |", "|---|---|---|---|---|"]
old = {s["name"]: s for s in json.load(open(os.path.join(SA, "..", "martial_arts", "martial_arts.json"), encoding="utf-8"))["chi"]}
for s in ST["spells"]:
    if s["name"] not in old: continue
    rows.append("| %s | %s | %s | %s | %s |" % (s["name"], f0(s["mana"]), f0(s["damage"]), " / ".join(f0(s["damage"] * (1 + MA["spell_power_per_tier"] * (t - 1))) for t in range(2, 6)), f0(round(old[s["name"]]["damage"] * 1.042))))
tables["chi"] = rows
# ---- the kits
rows = ["| Hero | Tier 2 | Tier 3 | Tier 4 | Tier 5 |", "|---|---|---|---|---|"]
for n, ks in B["kits"].items():
    cells = []
    for t in range(2, 6):
        k = ks.get(str(t), {}); bits = []
        for f_ in ("weapon", "armour", "shield"):
            if k.get(f_): bits.append(k[f_])
        bits += k.get("rings", [])
        if k.get("slash"): bits.append(k["slash"])
        if k.get("tomes"): bits.append("tomes: " + ", ".join(k["tomes"]))
        if k.get("army"): bits.append("%d of her best summoning called" % k["army"])
        cells.append(", ".join(bits) or "-")
    rows.append("| %s | %s |" % (TITLE.get(n, n), " | ".join(cells)))
tables["kits"] = rows
# ---- the trials
tp = os.path.join(SA, "test_%s.json" % TAG)
if os.path.exists(tp):
    R = json.load(open(tp, encoding="utf-8")); st = next((s for s in R["steps"] if s["step"] == "balance"), None)
    if st and st.get("trials"):
        rows = ["| Hero | Fight | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |", "|---|---|---|---|---|---|---|"]
        def cell(r):
            if not r: return "-"
            if r["won"]: return "won, %s s, %s %% left" % (f0(r["secs"]), f0(r["hp_left"] * 100))
            return ("down after %s s" % f0(r["secs"])) if r["down"] else "not done in %s s (%s left)" % (f0(r["secs"]), ", ".join(str(x) for x in r["left"]))
        def bosses(v):
            bs = v.get("bosses") or ([v["boss"]] if v.get("boss") else [])
            if not bs: return "-"
            won = [b for b in bs if b["won"]]
            s_ = "won %d of %d" % (len(won), len(bs))
            if won: s_ += " (%s s, %s %% left)" % (" / ".join(f0(b["secs"]) for b in won), " / ".join("under 1" if b["hp_left"] < 0.005 else f0(b["hp_left"] * 100) for b in won))
            return s_
        for h in ST["heroes"]:
            tr_ = [st["trials"].get("%s|%d" % (h["name"], t), {}) for t in range(1, 6)]
            rows.append("| %s | three of the tier | %s |" % (TITLE[h["name"]], " | ".join(cell(v.get("pack")) for v in tr_)))
            rows.append("|  | its boss | %s |" % " | ".join(bosses(v) for v in tr_))
        tables["trials"] = rows
p = os.path.join(ROOT, "docs", "levels", "mistward_castle.md"); s = open(p, encoding="utf-8").read()
for key, rows in tables.items():
    a, b = "<!-- mw6:%s -->" % key, "<!-- /mw6:%s -->" % key
    if s.count(a) != 1 or s.count(b) != 1: print("mw_balance: no markers for", key); continue
    s = re.sub(re.escape(a) + r".*?" + re.escape(b), lambda m: a + "\n" + "\n".join(rows) + "\n" + b, s, flags=re.S)
    print("mw_balance: %s, %d rows" % (key, len(rows) - 2))
open(p, "w", encoding="utf-8", newline="").write(s)
