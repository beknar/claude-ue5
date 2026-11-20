"""The user's list of 2026-11-20 (docs/improvements15.txt; the plan docs/improvements15_plan.md), in phases.

Parts (args):
  allies          the second phase (items 2, 3, 9, 30; C++ RD/RDList15.cpp): on every map the Summoner plays (the castle, the
                  dungeons copied from it and brokenspire), her allies solid to her and stepping aside (bAllySolid15,
                  bAllyYield15), the arena gathering them (bArenaAllies15, the maps with arenas), her summons answering in the wilds
                  (bWildSummons15, brokenspire). Off everywhere else (level 5's raised dead, the older levels: PR #94's review).
"""
import gc, sys
import unreal

eal = unreal.EditorAssetLibrary
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
REPORT = []
MAPS = "/Game/RandomDungeon/Maps/"
# (the maps of the game the Summoner plays: martial_arts is the Martial Artist's alone)
GAME_MAPS = ("brokenspire", "mistward_castle", "vel_morrath", "war_engine", "sewers", "kethrys_spire", "heaven_fortress")
args = [a for a in sys.argv[1:] if a in ("allies",)] or ["allies"]


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


if "allies" in args: each(GAME_MAPS, allies, "allies")
print("\n".join(REPORT))
del eal, eas, les, ues
gc.collect()
