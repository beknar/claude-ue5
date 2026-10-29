"""mistward_castle and random_dungeonmagic_level5 (the user's of 2026-10-28): the Mage's mana pool grows with two tomes.
Null Sanctum (220 mana) and Apocalypse (300) cost more than her pool can ever hold (100, x2 with the best Magic Potency
Ring): learning either tome makes her pool at least that much (FRDHeroDef::TomeMana; URDCombatComponent::UpdateMaxima,
GetTomeMana). The numbers are spells.json's `tome_mana`; a spell named there must be in the level's spell table.
Run on any level (it opens both, mistward_castle first, and ends on mistward_castle). Args: none"""
import json, os, unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem); les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\random_dungeon_magic5"
TM = {k: v for k, v in json.load(open(os.path.join(SA, "spells.json"), encoding="utf-8"))["tome_mana"].items() if not k.startswith("_")}
MAPS = ["/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/random_dungeonmagic_level5"]


def open_map(m):
    if not ues.get_editor_world().get_path_name().startswith(m + "."): les.load_level(m)
    w = ues.get_editor_world(); assert w.get_path_name().startswith(m + "."), w.get_path_name()
    return next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))


for MAP in MAPS:
    gen = open_map(MAP)
    spells = {str(s.name): s for s in gen.get_editor_property("spells")}
    heroes = list(gen.get_editor_property("heroes"))
    done = {}
    for h in heroes:
        want = TM.get(str(h.name), {})
        for nm, pool in want.items():
            assert nm in spells, f"{nm} is not in {MAP}'s spell table"
            assert pool >= spells[nm].mana, f"{nm}: a pool of {pool} is less than its {spells[nm].mana} mana"
        h.set_editor_property("tome_mana", {unreal.Name(k): float(v) for k, v in want.items()})
        if want: done[str(h.name)] = {k: (v, spells[k].mana) for k, v in want.items()}
    gen.set_editor_property("heroes", heroes)
    gen.modify()
    les.save_current_level()
    print(f"TOMEMANA {MAP.rsplit('/', 1)[1]}: " + "; ".join(f"{h}: " + ", ".join(f"{k} pool {p:.0f} (costs {m:.0f})" for k, (p, m) in d.items()) for h, d in done.items()))
open_map(MAPS[0])
import gc
for _n in [n for n in list(globals()) if not n.startswith("__") and n not in ("unreal", "gc")]: del globals()[_n]
gc.collect()
