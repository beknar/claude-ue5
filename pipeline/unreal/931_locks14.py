"""The user's list of 2026-11-16 (docs/improvements14.txt; the plan docs/improvements14_plan.md), its ninth phase (items 13 and
14): locked wild containers (the Rogue picks, the Warrior breaks, the others are refused), and the people who hear or see a lock
picked or broken turn on her. C++: RD/RDList14i.cpp.

Parts (args):
  data    brokenspire: bWildLocks14 on, and SourceArt/wilderness/locks14.json's share, pick time, hearing and seeing distances, a
          hostile person's blow and how far she must go for them to calm down. Idempotent (set anew).
"""
import json, os, sys, gc
import unreal

SA = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "SourceArt")
J = json.load(open(os.path.join(SA, "wilderness", "locks14.json"), encoding="utf-8"))
eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAPS = "/Game/RandomDungeon/Maps/"
REPORT = []


def each(maps, fn, label):
    for m in maps:
        if not eal.does_asset_exist(MAPS + m): REPORT.append(f"{label}: no map {m}"); continue
        les.load_level(MAPS + m); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
        what = fn(g)
        g.modify(); les.save_current_level()
        g = None; gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
        REPORT.append(f"931 {label} {m}: {what}")


def data_fn(g):
    g.set_editor_property("wild_locks14", True)
    g.set_editor_property("wild_lock_share14", float(J["share"]))
    g.set_editor_property("wild_pick_seconds14", float(J["pick_s"]))
    g.set_editor_property("wild_hear_cm14", float(J["hear_m"]) * 100.0)
    g.set_editor_property("wild_see_cm14", float(J["see_m"]) * 100.0)
    g.set_editor_property("wild_folk_blow14", float(J["blow"]))
    g.set_editor_property("wild_calm_cm14", float(J["calm_m"]) * 100.0)
    return f"locks on ({J['share']:.0%}), heard {J['hear_m']} m, seen {J['see_m']} m"


if "data" in sys.argv[1:]: each(J["maps"], data_fn, "data")
for line in REPORT: print(line)
gc.collect()
