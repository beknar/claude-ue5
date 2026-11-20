"""The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), in phases.

Parts (args):
  allies          the second phase (items 2, 3, 9, 30; C++ RD/RDList15.cpp): on every map the Summoner plays (the castle, the
                  dungeons copied from it and brokenspire), her allies solid to her and stepping aside (bAllySolid15,
                  bAllyYield15), the arena gathering them (bArenaAllies15, the maps with arenas), her summons answering in the wilds
                  (bWildSummons15, brokenspire). Off everywhere else (level 5's raised dead, the older levels: PR #94's review).
  summons         the third phase (item 18): each summoning's kinds (FRDSpellDef::SummonKinds) on every map she plays: its own kind
                  first, then four more of the same dungeon's table (the castle's, The War Engine's, the sewers', the tower's,
                  the fortress's: SourceArt/<dungeon>/monsters.json) nearest its tier (its own tier first; stronger first; never the
                  final boss), each one this map has with its mesh. Writes what it chose to SourceArt/balance/summons15.json.
  hands           the third phase (item 13): the Summoner's bare hands ("Bare Hands", bUnarmed15: no mesh, its attack refused) at
                  the end of her weapons on every map she plays.
  quick           the third phase (item 14): a scroll her hero can read goes on the quick bar (bQuickScrolls15) on every map of the
                  game and martial_arts.
"""
import gc, json, os, sys
import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
REPORT = []
MAPS = "/Game/RandomDungeon/Maps/"
# (the maps of the game the Summoner plays: martial_arts is the Martial Artist's alone)
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
PARTS = ("allies", "summons", "hands", "quick")
args = [a for a in sys.argv[1:] if a in PARTS] or list(PARTS)
SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
DUNGEONS = ("war_engine", "sewers", "kethrys_spire", "heaven_fortress")
FAMILY = {}
for d in DUNGEONS:
    for m in json.load(open(os.path.join(SA, d, "monsters.json"), encoding="utf-8"))["monsters"]: FAMILY[m["name"]] = d
CHOSEN = {}


def open_map(m):
    path = MAPS + m
    if not ues.get_editor_world().get_path_name().startswith(path + "."):
        les.load_level(path); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    w = ues.get_editor_world(); assert w.get_path_name().startswith(path + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        g = open_map(m)
        what = fn(g, m)
        g.modify(); les.save_current_level()
        # (the generator let go before the next map loads: one left in a variable made a load fatal (PR #78's review))
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"934 {label} {m}: {what}")


def allies(g, m):
    sets = {"ally_solid15": True, "ally_yield15": True, "arena_allies15": True, "wild_summons15": m == "brokenspire"}
    for k, v in sets.items(): g.set_editor_property(k, v)
    return {k: g.get_editor_property(k) for k in sets}


def summons(g, m):
    """each summoning's five kinds on this map (see the docstring)"""
    fb = str(g.get_editor_property("final_boss_kind"))
    mons = [d for d in g.get_editor_property("monsters") if d.get_editor_property("mesh")]
    tier = {str(d.name): d.tier for d in mons}
    sp = list(g.get_editor_property("spells")); out = {}
    # (a kind is offered by one summoning only: every summoning's own kind is taken first, then each one's four as they are chosen
    # (PR #95's review: Summon Tier 6 and 7, both of The War Engine's tier 3, offered the same five))
    used = {str(s.summon_kind) for s in sp if s.kind == unreal.RDSpellKind.SUMMON}
    for i, s in enumerate(sp):
        if s.kind != unreal.RDSpellKind.SUMMON: continue
        k0 = str(s.summon_kind)
        if k0 not in tier: out[str(s.name)] = f"no {k0} here"; continue
        fam = FAMILY.get(k0, "castle"); t0 = tier[k0]
        cand = [d for d in mons if FAMILY.get(str(d.name), "castle") == fam and str(d.name) != fb and str(d.name) not in used]
        cand.sort(key=lambda d: (abs(d.tier - t0), -d.get_editor_property("health_factor"), str(d.name)))
        kinds = [k0] + [str(d.name) for d in cand[:4]]
        used.update(kinds)
        s.set_editor_property("summon_kinds", [unreal.Name(k) for k in kinds]); sp[i] = s
        out[str(s.name)] = kinds
    g.set_editor_property("spells", sp)
    # (read back from the level: a struct out of a list is a copy)
    back = {str(s.name): [str(k) for k in s.get_editor_property("summon_kinds")] for s in g.get_editor_property("spells") if s.kind == unreal.RDSpellKind.SUMMON}
    assert all(back.get(k) == v for k, v in out.items() if isinstance(v, list)), "summon kinds not written"
    CHOSEN[m] = out
    return {k: (len(v) if isinstance(v, list) else v) for k, v in out.items()}


def hands(g, m):
    """her bare hands at the end of the Summoner's weapons (once)"""
    hs = list(g.get_editor_property("heroes"))
    i = next((k for k, h in enumerate(hs) if str(h.name) == "Summoner"), None)
    if i is None: return "no Summoner"
    h = hs[i]; ws = list(h.get_editor_property("weapons"))
    if not any(w.get_editor_property("unarmed15") for w in ws):
        w = unreal.RDWeaponDef(); w.set_editor_property("name", "Bare Hands"); w.set_editor_property("unarmed15", True)
        ws.append(w); h.set_editor_property("weapons", ws); hs[i] = h; g.set_editor_property("heroes", hs)
    h2 = next(h for h in g.get_editor_property("heroes") if str(h.name) == "Summoner")
    return [str(w.name) for w in h2.get_editor_property("weapons")]


def quick(g, m):
    g.set_editor_property("quick_scrolls15", True)
    return g.get_editor_property("quick_scrolls15")


if "allies" in args: each(GAME_MAPS, allies, "allies")
if "summons" in args:
    each(GAME_MAPS, summons, "summons")
    json.dump(CHOSEN, open(os.path.join(SA, "balance", "summons15.json"), "w", encoding="utf-8"), indent=1)
if "hands" in args: each(GAME_MAPS, hands, "hands")
if "quick" in args: each(GAME_MAPS + ("martial_arts",), quick, "quick")
print("\n".join(REPORT))
del eal, eas, les, ues
gc.collect()
