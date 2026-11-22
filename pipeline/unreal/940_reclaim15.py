"""reclaim15: the user's list of 2026-11-20 (docs/improvements15.txt, item 25: docs/wilderness_ideas.md's idea 6), its plan's fourteenth
phase: camps cleared that change the world (C++ RD/RDList15m.cpp). From SourceArt/wilderness/reclaim15.json: brokenspire's days before a
cleared camp's nearest ruin is resettled, the ruin's reach, the waypoint's trader (its body checked against the level's townsfolk) and lines,
and the settlers' lines. No arguments."""
import os, json, gc, unreal
MAPS = "/Game/RandomDungeon/Maps/"
SA = r"E:\code\claude-ue5\claude_ue5\SourceArt\wilderness"
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
J = json.load(open(os.path.join(SA, "reclaim15.json"), encoding="utf-8"))


def run():
    les.load_level(MAPS + "brokenspire"); unreal.SystemLibrary.execute_console_command(None, "obj gc")
    g = next(a for a in eas.get_all_level_actors() if isinstance(a, unreal.RDDungeonGenerator))
    defs = [str(d.get_editor_property("name")) for d in g.get_editor_property("townsfolk") if d.get_editor_property("mesh")]
    assert any(d.startswith(J["trader_def"]) for d in defs), ("no townsfolk body", J["trader_def"])
    for d in ("Townsman", "Townswoman", "Child"): assert any(x.startswith(d) for x in defs), ("the settlers need", d)
    assert J["days"] > 0 and J["trader_lines"] and J["settler_lines"]
    g.set_editor_property("reclaim_days15", float(J["days"]))
    g.set_editor_property("reclaim_ruin_km15", float(J["ruin_km"]))
    g.set_editor_property("reclaim_trader_def15", J["trader_def"])
    g.set_editor_property("reclaim_trader_lines15", J["trader_lines"])
    g.set_editor_property("reclaim_settler_lines15", J["settler_lines"])
    g.modify(); les.save_current_level()
    print(f"RECLAIM15 940 brokenspire: {J['days']} days, ruins within {J['ruin_km']} km, trader {J['trader_def']}, {len(J['settler_lines'])} settler lines")
    g = None


run()
gc.collect(); unreal.SystemLibrary.execute_console_command(None, "obj gc")
